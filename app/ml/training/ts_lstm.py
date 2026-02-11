import asyncio
import os
import joblib
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
from torch.utils.data import Dataset, DataLoader

from app.batch.models.job_unit import JobUnit
from app.core.config.config import get_config
from app.core.utils.logger import get_logger
from app.ml.core.models.training_run import RunStatus
from app.ml.data.models.ticker import Ticker
from app.ml.data.models.vw_ticker_timeseries import TickerTimeseries
from app.ml.model_defs.lstm import LSTMModel
from app.ml.training.trainable import Trainable

L = get_logger(__name__)

class Trainer(Trainable):
    def __init__(self):
        super().__init__()

    def run(self, unit):
        super().run(unit)
        try:
            asyncio.run(self._train(unit))
            self.training_run.status = RunStatus.COMPLETE
        except (RuntimeError, ValueError, torch.cuda.OutOfMemoryError) as e:
            L.error(f"Training failed: {str(e)}", exc_info=True)
            self.training_run.status = RunStatus.FAILED
            raise
        finally:
            self.training_run._update()

    async def _load(self) -> pd.DataFrame:
        ticker = await Ticker.findByTicker(self.config.get("ticker"))
        tts = await TickerTimeseries.findByTicker(ticker=ticker)
        df = pd.DataFrame([r.__dict__ for r in tts])
        return df.sort_values(by="date", ascending=False)

    async def _train(self, unit:JobUnit) -> LSTMModel:
        df = await self._load()
        gid_training_run = self.config.get("gid_training_run")
        ticker = self.config.get("ticker")
        f_cols = self.config.get("f_cols")
        epochs = self.config.get("epochs")
        hidden_size = self.config.get("hidden_size")
        num_layers = self.config.get("num_layers")
        dropout = self.config.get("dropout")
        batch_size = self.config.get("batch_size")
        learning_rate = self.config.get("learning_rate")
        weight_decay = self.config.get("weight_decay")
        patience = self.config.get("patience")
        grad_clip = self.config.get("grad_clip")
        train_split = self.config.get("train_split")

        # GPU support
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        L.info(f"Training on device: {device}")

        # Train/validation split (temporal - no shuffling!)
        train_size = int(train_split * len(df))
        train_df = df.iloc[:train_size]
        val_df = df.iloc[train_size:]

        L.info(f"Train size: {len(train_df)}, Validation size: {len(val_df)}")

        # Create datasets - validation reuses training scaler
        scaler_path = f"{get_config().obj_dir}/{gid_training_run}_scaler.pkl"
        train_dataset = TimeSeriesLSTM(
            train_df,
            scaler_path=scaler_path,
            ticker=ticker,
            feature_cols=f_cols
        )
        val_dataset = TimeSeriesLSTM(
            val_df,
            ticker=ticker,
            feature_cols=f_cols,
            scaler=train_dataset.scaler
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True if torch.cuda.is_available() else False
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=2,
            pin_memory=True if torch.cuda.is_available() else False
        )

        # Initialize model with dropout
        model = LSTMModel(
            input_size=len(train_dataset.f_cols),
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=len(train_dataset.f_cols),
            dropout=dropout
        ).to(device)

        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

        # Learning rate scheduler - reduces LR when validation loss plateaus
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5
        )

        # Early stopping setup
        best_val_loss = float('inf')
        best_epoch = 0
        patience_counter = 0

        # Metrics tracking
        train_losses = []
        val_losses = []
        learning_rates = []

        L.info(f"Starting training for {epochs} epochs...")

        for epoch in range(epochs):
            # Training phase
            model.train()
            train_loss = 0
            for x_batch, y_batch in train_loader:
                x_batch, y_batch = x_batch.to(device), y_batch.to(device)

                optimizer.zero_grad()
                y_pred = model(x_batch)
                loss:torch.Tensor = criterion(y_pred, y_batch)
                loss.backward()

                # Gradient clipping to prevent exploding gradients
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)

                optimizer.step()
                train_loss += loss.item()

            train_loss = train_loss / len(train_loader)

            # Validation phase
            model.eval()
            val_loss = 0
            with torch.no_grad():
                for x_batch, y_batch in val_loader:
                    x_batch, y_batch = x_batch.to(device), y_batch.to(device)
                    y_pred = model(x_batch)
                    loss = criterion(y_pred, y_batch)
                    val_loss += loss.item()

            val_loss = val_loss / len(val_loader)

            # Track metrics
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            current_lr = optimizer.param_groups[0]['lr']
            learning_rates.append(current_lr)

            unit.log(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, LR: {current_lr:.6f}")
            L.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, LR: {current_lr:.6f}")

            # Learning rate scheduling
            scheduler.step(val_loss)

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                patience_counter = 0
                # Save best model
                torch.save(model.state_dict(), f"{get_config().mdl_dir}/{gid_training_run}_best.pth")
                L.info(f"New best model saved! Val Loss: {best_val_loss:.6f}")
            else:
                patience_counter += 1

            if patience_counter >= patience:
                L.info(f"Early stopping triggered at epoch {epoch+1}. Best epoch was {best_epoch+1}")
                break

        # Load best model weights
        model.load_state_dict(torch.load(f"{get_config().mdl_dir}/{gid_training_run}_best.pth"))

        # Save final model and clean up checkpoint
        best_path = f"{get_config().mdl_dir}/{gid_training_run}_best.pth"
        torch.save(model.state_dict(), f"{get_config().mdl_dir}/{gid_training_run}.pth")
        os.remove(best_path)

        # Save training metrics
        metrics = {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'learning_rates': learning_rates,
            'best_epoch': best_epoch,
            'best_val_loss': best_val_loss,
            'final_train_loss': train_losses[-1],
            'final_val_loss': val_losses[-1]
        }
        joblib.dump(metrics, f"{get_config().obj_dir}/{gid_training_run}_metrics.pkl")

        unit.log(f"Training complete! Best Val Loss: {best_val_loss:.6f} at epoch {best_epoch+1}")
        L.info(f"Training complete! Best Val Loss: {best_val_loss:.6f} at epoch {best_epoch+1}")

        return model

    def get_class_name(self):
        return f"{__name__}.Trainer"

class TimeSeriesLSTM(Dataset):

    NAME = "TimeSeriesLSTM"

    def __init__(self, df:pd.DataFrame, ticker:str, seq_len:int=10, feature_cols:list[str]=None, scaler:MinMaxScaler=None, scaler_path:str=None):
        self.seq_len = seq_len
        self.f_cols = feature_cols
        self.ticker = ticker

        features = df[self.f_cols].values

        # Use provided scaler (for validation) or create new one (for training)
        if scaler is not None:
            self.scaler = scaler
            scaled = self.scaler.transform(features)
        else:
            self.scaler = MinMaxScaler()
            scaled = self.scaler.fit_transform(features)
            if scaler_path:
                joblib.dump(self.scaler, scaler_path)

        self.data = torch.tensor(scaled, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.data) - self.seq_len

    def __getitem__(self, index) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.data[index:index + self.seq_len]
        y = self.data[index + self.seq_len][:]
        return x, y
