class Job:
    config:dict[str, str] = {}

    def run(self) -> None: ...

    def configure(self, config) -> None:
        self.config = config