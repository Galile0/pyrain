from utils import reverse_bytewise, BOOL, ParsingException

# God damn I wish python had fall through like any normal switch-case syntax <.<
# But you know, explicit is better than implicit...yeah, fuck you
parsing = {  # thanks to https://github.com/jjbott/RocketLeagueReplayParser/ he has done a shitton of work on this
    #  Flagged int Properties (At least i assume its a flag + 32 bit int)
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
    "TAGame.Team_TA:LogoData": lambda x: _read_flagged_int(x),

    # 32 Bit int properties, seems to make sense
    "TAGame.GameEvent_Soccar_TA:SecondsRemaining": lambda x: _read_int(x),
    "TAGame.GameEvent_TA:ReplicatedGameStateTimeRemaining": lambda x: _read_int(x),
    "TAGame.CrowdActor_TA:ReplicatedCountDownNumber": lambda x: _read_int(x),
    "TAGame.GameEvent_Team_TA:MaxTeamSize": lambda x: _read_int(x),
    "Engine.PlayerReplicationInfo:PlayerID": lambda x: _read_int(x),
    "TAGame.PRI_TA:TotalXP": lambda x: _read_int(x),
    "TAGame.PRI_TA:MatchScore": lambda x: _read_int(x),
    "TAGame.GameEvent_Soccar_TA:RoundNum": lambda x: _read_int(x),
    "TAGame.GameEvent_TA:BotSkill": lambda x: _read_int(x),
    "TAGame.PRI_TA:MatchShots": lambda x: _read_int(x),
    "TAGame.PRI_TA:MatchSaves": lambda x: _read_int(x),
    "ProjectX.GRI_X:ReplicatedGamePlaylist": lambda x: _read_int(x),
    "Engine.TeamInfo:Score": lambda x: _read_int(x),
    "Engine.PlayerReplicationInfo:Score": lambda x: _read_int(x),
    "TAGame.PRI_TA:MatchGoals": lambda x: _read_int(x),
    "TAGame.PRI_TA:MatchAssists": lambda x: _read_int(x),
    "ProjectX.GRI_X:ReplicatedGameMutatorIndex": lambda x: _read_int(x),
    "TAGame.PRI_TA:Title": lambda x: _read_int(x),

    #  Single Byte Properties
    "Engine.PlayerReplicationInfo:Ping": lambda x: _read_byte(x),
    "TAGame.Vehicle_TA:ReplicatedSteer": lambda x: _read_byte(x),
    "TAGame.Vehicle_TA:ReplicatedThrottle": lambda x: _read_byte(x),
    "TAGame.PRI_TA:CameraYaw": lambda x: _read_byte(x),
    "TAGame.PRI_TA:CameraPitch": lambda x: _read_byte(x),
    "TAGame.Ball_TA:HitTeamNum": lambda x: _read_byte(x),
    "TAGame.GameEvent_Soccar_TA:ReplicatedScoredOnTeam": lambda x: _read_byte(x),

    #  Boolean Properties
    "Engine.Actor:bCollideWorld": lambda x: _read_bool(x),
    "Engine.PlayerReplicationInfo:bReadyToPlay": lambda x: _read_bool(x),
    "TAGame.Vehicle_TA:bReplicatedHandbrake": lambda x: _read_bool(x),
    "TAGame.Vehicle_TA:bDriving": lambda x: _read_bool(x),
    "Engine.Actor:bNetOwner": lambda x: _read_bool(x),
    "Engine.Actor:bBlockActors": lambda x: _read_bool(x),
    "TAGame.GameEvent_TA:bHasLeaveMatchPenalty": lambda x: _read_bool(x),
    "TAGame.PRI_TA:bUsingBehindView": lambda x: _read_bool(x),
    "TAGame.PRI_TA:bUsingSecondaryCamera": lambda x: _read_bool(x),
    "TAGame.GameEvent_TA:ActivatorCar": lambda x: _read_bool(x),
    "TAGame.GameEvent_Soccar_TA:bOverTime": lambda x: _read_bool(x),
    "ProjectX.GRI_X:bGameStarted": lambda x: _read_bool(x),
    "Engine.Actor:bCollideActors": lambda x: _read_bool(x),
    "TAGame.PRI_TA:bReady": lambda x: _read_bool(x),
    "TAGame.RBActor_TA:bFrozen": lambda x: _read_bool(x),
    "Engine.Actor:bHidden": lambda x: _read_bool(x),
    "Engine.Actor:bTearOff": lambda x: _read_bool(x),
    "TAGame.CarComponent_FlipCar_TA:bFlipRight": lambda x: _read_bool(x),
    "Engine.PlayerReplicationInfo:bBot": lambda x: _read_bool(x),
    "Engine.PlayerReplicationInfo:bWaitingPlayer": lambda x: _read_bool(x),
    "TAGame.RBActor_TA:bReplayActor": lambda x: _read_bool(x),
    "TAGame.PRI_TA:bIsInSplitScreen": lambda x: _read_bool(x),
    "Engine.GameReplicationInfo:bMatchIsOver": lambda x: _read_bool(x),
    "TAGame.CarComponent_Boost_TA:bUnlimitedBoost": lambda x: _read_bool(x),

    # FLoat Properties
    "TAGame.CarComponent_FlipCar_TA:FlipCarTime": lambda x: _read_float(x),
    "TAGame.Ball_TA:ReplicatedBallScale": lambda x: _read_float(x),
    "TAGame.CarComponent_Boost_TA:RechargeDelay": lambda x: _read_float(x),
    "TAGame.CarComponent_Boost_TA:RechargeRate": lambda x: _read_float(x),
    "TAGame.Ball_TA:ReplicatedAddedCarBounceScale": lambda x: _read_float(x),
    "TAGame.Ball_TA:ReplicatedBallMaxLinearSpeedScale": lambda x: _read_float(x),
    "TAGame.Ball_TA:ReplicatedWorldBounceScale": lambda x: _read_float(x),
    "TAGame.CarComponent_Boost_TA:BoostModifier": lambda x: _read_float(x),
    "Engine.Actor:DrawScale": lambda x: _read_float(x),
    "TAGame.CrowdActor_TA:ModifiedNoise": lambda x: _read_float(x),

    # String Properties
    "Engine.GameReplicationInfo:ServerName": lambda x: _read_string(x),
    "Engine.PlayerReplicationInfo:PlayerName": lambda x: _read_string(x),
    "TAGame.Team_TA:CustomTeamName": lambda x: _read_string(x)
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


def _read_byte(bitstream):
    return reverse_bytewise(bitstream.read('bits:8')).uintle


def _read_bool(bitstream):
    return bitstream.read(BOOL)


def _read_float(bitstream):
    return reverse_bytewise(bitstream.read('bits:32')).floatle


def _read_string(bitstream):  # Kinda copypasta from utils.read_string ... not feelin to good about this :/
    length = _read_int(bitstream)*8
    if length < 0:
        length *= -2 # Thats hard to read, maybe I should untangle it? eh whatever TODO untangle
        return reverse_bytewise(bitstream.read('bits:'+str(length))).bytes[:-2].decode('utf-16')
    return reverse_bytewise(bitstream.read('bits:'+str(length))).bytes[:-1].decode('utf-8')
