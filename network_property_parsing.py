from utils import reverse_bytewise, BOOL, ParsingException


parsing = {
    "TAGame.Team_TA:GameEvent": lambda x: _read_flagged_int(x),
    "TAGame.CrowdActor_TA:ReplicatedOneShotSound": lambda x: _read_flagged_int(x),
    "TAGame.CrowdManager_TA:ReplicatedGlobalOneShotSound": lambda x: _read_flagged_int(x),
    "Engine.Actor:Owner": lambda x: _read_flagged_int(x),
    "Engine.GameReplicationInfo:GameClass": lambda x: _read_flagged_int(x),
    "Engine.PlayerReplicationInfo:Team": lambda x: _read_flagged_int(x),
    "TAGame.CrowdManager_TA:GameEvent": lambda x: _read_flagged_int(x),
    "Engine.Pawn:PlayerReplicationInfo": lambda x: _read_flagged_int(x),
    "TAGame.PRI_TA:ReplicatedGameEvent": lambda x: _read_flagged_int(x),
    "TAGame.Ball_TA:GameEvent": lambda x: _read_flagged_int(x),
    "Engine.Actor:ReplicatedCollisionType": lambda x: _read_flagged_int(x),
    "TAGame.CrowdActor_TA:GameEvent": lambda x: _read_flagged_int(x),
    "TAGame.Team_TA:LogoData": lambda x: _read_flagged_int(x)
}


def read_property_value(property_name, bitstream):
    try:
        value = parsing[property_name](bitstream)
    except KeyError:
        raise ParsingException("Dont know how to parse bits for %s \n Have some raw Bits: %s"
                               % (property_name, bitstream.read('hex:128')))
    return value


def _read_flagged_int(bitstream):
    flag = bitstream.read(BOOL)
    num = _read_int(bitstream)
    return flag, num


def _read_int(bitstream):
    return reverse_bytewise(bitstream.read('bits:32')).uintle
