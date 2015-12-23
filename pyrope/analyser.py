class Analyser:

    def __init__(self, replay):
        if not replay.netstream:
            raise TypeError("Replay has to be decoded")
        self.replay = replay
        self.player = self._get_player()

    def _get_player(self):  # Todo add check that frames are actually parsed
        player = {}
        for frame in self.replay.netstream.values():
            for name, value in frame.actors.items():
                if "e_Default__PRI_TA" in name:
                    try:
                        player[value['data']['Engine.PlayerReplicationInfo:PlayerName']] = value['actor_id']
                    except KeyError:
                        pass
        return player

    def get_player_pos(self, player, sep=False):
        playerid = self.player[player]
        current_car = -1
        car_actors = []
        frame_left = max(self.replay.netstream, key=int)  # Assume player left never, or after last frame
        player_spawned = False
        frame_entered = 0
        for i, frame in self.replay.netstream.items():
            found_pos = False
            for actor in frame.actors.values():
                try:
                    if actor['data']["Engine.Pawn:PlayerReplicationInfo"][1] == playerid:
                        current_car = actor['actor_id']
                except KeyError:
                    pass
                if actor['actor_id'] == current_car:
                    try:
                        pos = actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos']
                        car_actors.append(pos)
                        found_pos = True
                        if not player_spawned:
                            player_spawned = True
                            frame_entered = i
                    except KeyError:
                        pass
            if not found_pos and player_spawned:
                car_actors.append(car_actors[-1])
            try:
                if frame.actors[str(playerid) + 'e_Default__PRI_TA']\
                        ['data']['Engine.PlayerReplicationInfo:Team'][1] == -1:
                    # Player got assigned team -1 that means he left the game early
                    frame_left = i
                    break
            except KeyError:
                pass
        result = []
        if sep:
            slice_frames = [v['frame'] - frame_entered for v in self.replay.header['Goals'] if
                            frame_entered <= v['frame'] <= frame_left]
            slice_frames.append(frame_left - frame_entered)
            lastframe = 0
            for framenum in slice_frames:
                result.append({'player': player,
                               'start': self.replay.netstream[lastframe].current,
                               'end': self.replay.netstream[framenum].current,
                               'data': car_actors[lastframe:framenum]})
                lastframe = framenum
        else:
            result.append({'player': player,
                           'start': self.replay.netstream[frame_entered].current,
                           'end': self.replay.netstream[frame_left].current,
                           'data': car_actors[:-1]})
        return result

    def get_ball_pos(self):
        result = []
        for num, frame in self.replay.netstream.items():
            for actor in frame.actors.values():
                if "Ball_Default" in actor['actor_type']:
                    try:
                        pos = actor['data']['TAGame.RBActor_TA:ReplicatedRBStat']['pos']
                        result.append(pos)
                    except KeyError:
                        pass
        return result


class AnalyserUtils:
    @staticmethod
    def filter_coords(coords):
        result = []
        for i, coord in enumerate(coords):
            y = [x for x, y, z in coord['data'] if z > 15 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
            x = [y for x, y, z in coord['data'] if z > 15 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
            if not x and y:
                raise ValueError('No points found')
            player = coord['player']
            if len(player) > 20:
                player = player[0:9] + ' ... ' + player[-6:]
            title = "%s From: %ds To: %ds" % (player, coord['start'], coord['end'])
            title_short = "%s [%d - %d]" % (coord['player'], coord['start'], coord['end'])
            result.append({'x': x,
                           'y': y,
                           'title': title,
                           'title_short': title_short})
        return result
