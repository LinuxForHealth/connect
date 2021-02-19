import xworkflows

class CoreWorkflowDef(xworkflows.Workflow):
    """
    Implements the base LinuxForHealth workflow definition.
    """
    states = (
        ('parse', "Parse"),
        ('validate', "Validate"),
        ('transform', "Transform"),
        ('persist', "Persist"),
        ('transmit', "Transmit"),
        ('sync', "Synchronize"),
        ('error', "Error")
    )

    transitions = (
        ('do_validate', 'parse', 'validate'),
        ('do_transform', 'validate', 'transform'),
        ('do_persist', ('parse', 'validate', 'transform'), 'persist'),
        ('do_transmit', 'persist', 'transmit'),
        ('do_sync', ('persist', 'transmit'), 'sync'),
        ('handle_error', ('parse', 'validate', 'transform', 'persist', 'transmit', 'sync'), 'error')
    )

    initial_state = 'parse'

class CoreWorkflow(xworkflows.WorkflowEnabled):
    """
    Implements the base LinuxForHealth workflow.
    """
    def __init__(self, message):
        self.message = message

    state = CoreWorkflowDef()

    @xworkflows.transition('do_validate')
    def validate(self):
        """
        Override to send the message to a NATS subscriber for validation.
        """
        print("Override to validate message: ", self.message)

    @xworkflows.transition('do_transform')
    def transform(self):
        """
        Override to send the message to a NATS subscriber for optional transformation from one
        form or protocol to another (e.g. HL7v2 to FHIR or FHIR R3 to R4).
        """
        print("Transforming message: ", self.message)

    @xworkflows.transition('do_persist')
    def persist(self):
        """
        Send the message to a NATS subscriber for persistence, including transformation of
        the message to the LinuxForHealth data storage format.
        """
        # Provide default persistence in Kafka in CoreWorkflow
        print("Persisting message: ", self.message)

    @xworkflows.transition('do_transmit')
    def transmit(self):
        """
        Send the message to a NATS subscriber for transmission to an external service via HTTP.
        """
        # Provide default http transmission in CoreWorkflow, but do not include in run()
        # Create property for HTTP target.
        print("Transmitting message: ", self.message)

    @xworkflows.transition('do_sync')
    def synchronize(self):
        """
        Send the message to a NATS subscriber for synchronization across LFH instances.
        """
        # Provide default NATS record publish
        print("Synchronizing message: ", self.message)

    @xworkflows.transition('handle_error')
    def error(self):
        """
        Send the message to a NATS subscriber to record errors.
        """
        # Provide default NATS error publish
        print("Processing error: ", self.message)

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
            print("State after transmit = ", self.state)
            # Transition from transmit to sync
            self.synchronize()
            print("CoreWorkflow complete: final state = ", self.state)
            return self.message
        except Exception as ex:
            print("State before error transition:", self.state)
            self.error()
            print("Received exception: ", ex, "State after error:", self.state)
            raise
