class FlowManager:

    def __init__(self):
        self.current_flow = None

    def start(self, flow):
        self.current_flow = flow

    def stop(self):
        self.current_flow = None

    def is_active(self, flow):
        return self.current_flow == flow


flow_manager = FlowManager()