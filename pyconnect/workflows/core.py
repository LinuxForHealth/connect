import xworkflows

class CoreWorkflowDef(xworkflows.Workflow):

    states = (
        ('parse', "Parse"),
        ('validate', "Validate"),
        ('transform', "Transform"),
        ('persist', "Persist"),
        ('transmit', "Transmit")
    )

    transitions = (
        ('do_validate', 'parse', 'validate'),
        ('do_transform', 'validate', 'transform'),
        ('do_persist', 'transform', 'persist'),
        ('do_transmit', 'persist', 'transmit')
    )

    initial_state = 'parse'


class CoreWorkflow(xworkflows.WorkflowEnabled):

    def __init__(self, message):
        self.message = message

    state = CoreWorkflowDef()

    @xworkflows.transition('do_validate')
    def validate(self):
        print("Validated message: ", self.message)
        return self.message

    @xworkflows.transition('do_transform')
    def transform(self):
        print("Transformed message: ", self.message)
        return self.message

    @xworkflows.transition('do_persist')
    def persist(self):
        print("Persisted message: ", self.message)
        return self.message

    @xworkflows.transition('do_transmit')
    def transmit(self):
        print("Transmitted message: ", self.message)
        return self.message

    def run(self):
        print("Running CoreWorkflow, starting state=", self.state)
        # Transition from parse to validate
        self.validate()
        print("State = ", self.state)
        # Transition from validate to transform
        self.transform()
        print("State = ", self.state)
        # Transition from transform to persist
        self.persist()
        print("State = ", self.state)
        # Transition from persist to transmit
        self.transmit()
        print("CoreWorkflow complete: finished state = ", self.state)
        return self.message
