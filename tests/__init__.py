from connect.server_handlers import add_trace_logging
import os

add_trace_logging()

# base resource directory for "file fixtures" (sample x12 transactions)
resources_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "resources",
)
