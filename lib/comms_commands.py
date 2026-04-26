from core.comms.mesh import mesh
from core.config import get_config
from constants import C_MESH_PING, SECURITY_NODE_ID_CONFIG


async def ping(timeout: float = 5.0) -> bool:
    """
    Check if the  security-node response.

    :returns:  True, when an ack was received else it times-out and returns False
    """
    m = mesh()
    cfg = get_config()

    _node_id = cfg.get(SECURITY_NODE_ID_CONFIG)

    if _node_id is None:
        raise ValueError(f"Security Node id value for config.toml path: {SECURITY_NODE_ID_CONFIG} not set")

    _ , _seq = await m.async_send_data(_node_id,C_MESH_PING,True)

    return await m.async_wait_for_ack(_node_id,_seq,timeout)

