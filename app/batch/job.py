class Job:
    config:dict[str, str] = {}

    def run(self) -> None:
        """
            TODO - eventually pass in some sort of job unit reference
        """
        raise NotImplementedError("Child must implement this method")

    def configure(self, config:dict) -> None:
        self.config = config

    def get_class_name(self) -> str:
        raise NotImplementedError("Child must implement this method")