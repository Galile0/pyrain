import numpy as np


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
                if ("e_Default__PRI_TA" in name and
                        "Engine.PlayerReplicationInfo:Team" in value['data']):
                    try:
                        playername = value['data']['Engine.PlayerReplicationInfo:PlayerName']
                        actorid = value['actor_id']
                        if playername in player:
                            if actorid not in player[playername]['cars']:
                                player[playername]['cars'].append(value['actor_id'])
                        else:  # This will break if player of team a leaves and rejoins team b
                            teamid = value['data']['Engine.PlayerReplicationInfo:Team'][1]
                            player[playername] = {'cars': [value['actor_id']],
                                                  'team': teamid}
                    except KeyError:
                        pass
        team_ids = [v['team'] for k, v in player.items()]
        id_max = max(team_ids)
        id_min = min(team_ids)
        for k, v in player.items():  # Normalize Team Ids to 0 and 1
            if v['team'] == id_min:
                v['team'] = 0
            elif v['team'] == id_max:
                v['team'] = 1
            else:
                raise ValueError("THREE TEAMS?! NOT POSSIBLE!")
        return player

    def get_player_pos(self, player, sep=False):
        playerids = self.player[player]['cars']
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
                    actor_data = frame.actors[str(playerid) + 'e_Default__PRI_TA']['data']
                    if actor_data['Engine.PlayerReplicationInfo:Team'][1] == -1:
                        # Player got assigned team -1 that means he left the game early
                        frame_left = i
                        break
                except KeyError:
                    pass
            result.extend(self._wrap_data(player, car_actors, frame_entered, frame_left, sep))
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
        result = self._wrap_data('Ball', data, 0, max(self.replay.netstream, key=int), sep)
        return result

    def _wrap_data(self, player, data, start, end, slicing=False):
        result = []
        if slicing:
            slice_frames = [v['frame'] for v in self.replay.header['Goals'] if
                            start <= v['frame'] <= end]
            slice_frames.append(end)
            lastframe = start
            for framenum in slice_frames:
                result.append({'player': player,
                               'start': self.replay.netstream[lastframe].current,
                               'end': self.replay.netstream[framenum].current,
                               'frame_start': lastframe,
                               'frame_end': framenum,
                               'data': data[lastframe:framenum]})
                lastframe = framenum
        else:
            result.append({'player': player,
                           'start': self.replay.netstream[start].current,
                           'end': self.replay.netstream[end].current,
                           'frame_start': start,
                           'frame_end': end,
                           'data': data[:-1]})
        return result

    def calc_dist_to_zero(self, player, reference=None):
        if player == 'Ball':
            data_p = self.get_ball_pos()
        else:
            data_p = self.get_player_pos(player)
        vec_p = np.array(data_p[0]['data'])
        if reference:
            if reference == 'Ball':
                data_r = self.get_ball_pos()
            else:
                data_r = self.get_player_pos(reference)
            start = max(data_p[0]['frame_start'], data_r[0]['frame_start'])
            end = min(data_p[0]['frame_end'], data_r[0]['frame_end'])
            delta = end - start
            pstart = start - data_p[0]['frame_start']
            rstart = start - data_r[0]['frame_start']
            pend = pstart + delta
            rend = rstart + delta
            vec_p = vec_p[pstart:pend]
            vec_r = np.array(data_r[0]['data'][rstart:rend])
            timeline = np.linspace(max(data_p[0]['start'], data_r[0]['start']),
                                   min(data_p[0]['end'], data_r[0]['end']),
                                   end - start)
            distances = np.linalg.norm(vec_r - vec_p, axis=1)
        else:
            timeline = np.linspace(data_p[0]['start'], data_p[0]['end'],
                                   data_p[0]['frame_end'] - data_p[0]['frame_start'])
            distances = np.linalg.norm(vec_p, axis=1)
        result = {'xs': timeline,
                  'ys': distances}
        # print(len(result))
        return result


class AnalyserUtils:
    @staticmethod
    def filter_coords(coords):
        result = []
        for i, coord in enumerate(coords):  # TODO This may exlude the borders of Wasteland map
            y = [x for x, y, z in coord['data'] if
                 z > 0 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
            x = [y for x, y, z in coord['data'] if
                 z > 0 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
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
