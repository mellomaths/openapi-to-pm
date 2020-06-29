class Tracer:
    """
    Responsible to handle logging inside functions on script
    """

    def __init__(self, namespace):
        self.namespace = namespace
        self.messages = []

    def trace(self, msg):
        message = f'>>> {self.namespace}:: {msg}'
        self.messages.append(message)

    def log(self):
        for msg in self.messages:
            print(msg)
