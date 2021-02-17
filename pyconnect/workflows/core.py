import xworkflows

class CoreWorkflowDef(xworkflows.Workflow):

    states = (
        ('parse', "Parse"),
        ('validate', "Validate"),
        ('transform', "Transform"),
        ('persist', "Persist"),
        ('transmit', "Transmit"),
        ('error', "Error")
    )

    transitions = (
        ('do_validate', 'parse', 'validate'),
        ('do_transform', 'validate', 'transform'),
        ('do_persist', 'transform', 'persist'),
        ('do_transmit', 'persist', 'transmit'),
        ('handle_error', ('parse', 'validate', 'transform', 'persist', 'transmit'), 'error')
    )

    initial_state = 'parse'


class CoreWorkflow(xworkflows.WorkflowEnabled):

    def __init__(self, message):
        self.message = message
        self.original_message = message

    state = CoreWorkflowDef()

    @xworkflows.transition('do_validate')
    def validate(self):
        print("Validated message: ", self.message)

    @xworkflows.transition('do_transform')
    def transform(self):
        message = self.message
        print("Transformed message: ", message)
        self.message = message

    @xworkflows.transition('do_persist')
    def persist(self):
        print("Persisted message: ", self.message)

    @xworkflows.transition('do_transmit')
    def transmit(self):
        print("Transmitting message: ", self.message)
        # raise Exception('Error transmitting message', 'connection error')

    @xworkflows.transition('handle_error')
    def error(self):
        print("Error during state transition. error: ", self.message)

    def run(self):
        try:
            print("Running CoreWorkflow, starting state=", self.state)
            # Transition from parse to validate
            self.validate()
            print("State after validate = ", self.state)
            # Transition from validate to transform
            self.transform()
            print("State after transform = ", self.state)
            # Transition from transform to persist
            self.persist()
            print("State after persist = ", self.state)
            # Transition from persist to transmit
            self.transmit()
            print("CoreWorkflow complete: final state = ", self.state)
            return self.message
        except Exception as ex:
            print("State before error transition:", self.state)
            self.error()
            print("Received exception: ", ex, "State after error:", self.state)
            raise
