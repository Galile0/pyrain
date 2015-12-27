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
                if "e_Default__PRI_TA" in name and "TAGame.PRI_TA:ClientLoadout" in value['data']:
                    try:
                        playername = value['data']['Engine.PlayerReplicationInfo:PlayerName']
                        actorid = value['actor_id']
                        if playername in player:
                            if actorid not in player[playername]:
                                player[playername].append(value['actor_id'])
                        else:
                            player[playername] = [value['actor_id']]
                    except KeyError:
                        pass
        return player

    def get_player_pos(self, player, sep=False):
        playerids = self.player[player]
        result = []
        for playerid in playerids:
            current_car = -1
            car_actors = []
            frame_left = max(self.replay.netstream, key=int)
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
            result.extend(self.wrap_data(player, car_actors, frame_entered, frame_left, sep))
        return result

    def get_ball_pos(self, sep=False):
        data = []
        for num, frame in self.replay.netstream.items():
            found_ball = False
            for actor in frame.actors.values():
                if "Ball_Default" in actor['actor_type']:
                    try:
                        pos = actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos']
                        data.append(pos)
                        found_ball = True
                    except KeyError:
                        pass
            if not found_ball and data:
                data.append(data[-1])
        result = self.wrap_data('Ball', data, 0, max(self.replay.netstream, key=int), sep)
        return result

    def wrap_data(self, player, data, start, end, slice=False):
        result = []
        if slice:
            slice_frames = [v['frame'] - start for v in self.replay.header['Goals'] if start <= v['frame'] <= end]
            slice_frames.append(end - start)
            lastframe = 0
            for framenum in slice_frames:
                result.append({'player': player,
                               'start': self.replay.netstream[lastframe].current,
                               'end': self.replay.netstream[framenum].current,
                               'data': data[lastframe:framenum]})
                lastframe = framenum
        else:
            result.append({'player': player,
                           'start': self.replay.netstream[start].current,
                           'end': self.replay.netstream[end].current,
                           'data': data[:-1]})
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
