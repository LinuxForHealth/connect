import xworkflows
from pyconnect.workflows import core

class FhirWorkflow(core.CoreWorkflow):
    """
    Implements a FHIR validation and storage workflow for LinuxForHealth.
    """
    async def run(self):
        try:
            # TODO: Use LFH logging
            print("Running CoreWorkflow, starting state=", self.state)
            await self.persist()
            self.transmit()
            self.synchronize()
            return self.message
        except Exception as ex:
            self.error(ex)
            raise
