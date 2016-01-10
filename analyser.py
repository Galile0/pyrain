import numpy as np
from collections import OrderedDict


class Analyser:
    def __init__(self, replay):
        if not replay.netstream:
            raise TypeError("Replay has to be decoded")
        self.replay = replay
        self.player_data = OrderedDict(sorted(self._get_player().items()))

    def get_actor_pos(self, name, sep=False):
        if name == 'Ball':
            pos = self._get_ball_pos(sep)
        else:
            pos = self._get_player_pos(name, sep)
        return pos

    def _get_player(self):
        players = {}
        maxframe = max(self.replay.netstream, key=int)
        for i, frame in self.replay.netstream.items():
            pri_ta = [value for name, value in frame.actors.items() if 'e_Default__PRI_TA' in name]
            for value in pri_ta:
                teamid = None
                actorid = value['actor_id']
                try:
                    teamid = value['data']['Engine.PlayerReplicationInfo:Team'][1]
                except KeyError: pass
                try:
                    playername = value['data']['Engine.PlayerReplicationInfo:PlayerName']
                    if playername in players:  # Player already exists
                        if not any(actorid in data[playername]['id']
                                   for data in players[playername]):
                            players[playername].append({'id': actorid,
                                                        'join': i,
                                                        'left': maxframe,
                                                        'team': teamid})
                    elif 'TAGame.PRI_TA:ClientLoadout' in value['data']:
                        players[playername] = [{'id': actorid,
                                                'join': i,
                                                'left': maxframe,
                                                'team': teamid}]
                except KeyError:
                    pass
                if teamid == -1:
                    for actors in players.values():
                        for actor in actors:
                            if actorid == actor['id']:
                                actor['left'] = i
        return players

    def _get_player_pos(self, player, sep=False):
        actors = self.player_data[player]
        result = []
        for actor in actors:
            current_car = -1
            car_actors = []
            frame_left = max(self.replay.netstream, key=int)
            player_spawned = False
            frame_entered = 0
            for i in range(actor['join'], actor['left']+1):
                frame = self.replay.netstream[i]
                found_pos = False
                for f_actor in frame.actors.values():
                    try:
                        if f_actor['data']['Engine.Pawn:PlayerReplicationInfo'][1] == actor['id']:
                            current_car = f_actor['actor_id']
                    except KeyError:
                        pass
                    if f_actor['actor_id'] == current_car:
                        try:
                            pos = f_actor['data']['TAGame.RBActor_TA:ReplicatedRBState']['pos']
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
                    actor_data = frame.actors[str(actor['id']) + 'e_Default__PRI_TA']['data']
                    if actor_data['Engine.PlayerReplicationInfo:Team'][1] == -1:
                        # Player got assigned team -1 that means he left the game early
                        frame_left = i
                        break
                except KeyError:
                    pass
            result.extend(self._wrap_data(player, car_actors, frame_entered, frame_left, sep))
        return result

    def _get_ball_pos(self, sep=False):
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
                               'data': data[lastframe-start:framenum-start]})
                lastframe = framenum
        else:
            result.append({'player': player,
                           'start': self.replay.netstream[start].current,
                           'end': self.replay.netstream[end].current,
                           'frame_start': start,
                           'frame_end': end,
                           'data': data[:-1]})
        return result

    def calc_dist(self, player, reference=None):
        data_p = self.get_actor_pos(player)
        vec_p = np.array(data_p[0]['data'])  # TODO that only views single Player Ids (no rejoin?)
        if reference:
            data_r = self.get_actor_pos(reference)
            start = max(data_p[0]['frame_start'], data_r[0]['frame_start'])
            end = min(data_p[0]['frame_end'], data_r[0]['frame_end'])
            delta = end - start
            if delta <= 0:
                raise ValueError('Actors do not Overlap')
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
        result = {'time': timeline,
                  'distance': distances}
        return result


class AnalyserUtils:
    @staticmethod
    def filter_coords(coords, x, y, z):
        result = []
        for coord in coords:
            player = coord['player']
            if len(player) > 20:
                player = player[0:9] + ' ... ' + player[-6:]
            title = "%s From: %ds To: %ds" % (player, coord['start'], coord['end'])
            title_short = "%s [%d - %d]" % (coord['player'], coord['start'], coord['end'])
            result.append({'title': title,
                           'title_short': title_short})
            if y:
                y_coords = [x for x, y, z in coord['data'] if z > 0]
                result[-1]['y'] = y_coords
            if x:
                x_coords = [y for x, y, z in coord['data'] if z > 0]
                result[-1]['x'] = x_coords
            if z:
                z_coords = [z for x, y, z in coord['data'] if z > 0]
                result[-1]['z'] = z_coords
            if not len(x_coords) == len(y_coords):
                raise ValueError('Wrong Dimensions')
        return result
