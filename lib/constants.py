from micropython import  const


# Custom config.toml paths

SECURITY_NODE_ID_CONFIG = const("comms.mesh.security_node_id")

# Mesh Commands:
# Commands on this application layer are string based.
# A command with execution demand starts with prefix C:: followed by the command.

C_MESH_PING = const("C::PING")
