import csv
import json
import time


def epoch_to_string(epoch_timestamp):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.localtime(epoch_timestamp))
    # "2021-04-24T15:45:43.000Z"

class Episode:
    def __init__(self, season, episode, watched_at):
        self.season = season
        self.episode = episode
        self.watched_at = watched_at

    def get_season(self):
        return self.season

    def get_episode(self):
        return self.episode

    def get_watched_at(self):
        return self.watched_at


class Show:
    def __init__(self, name, year):
        self.name = name
        self.year = year
        self.seasons = []
    
    def get_name(self):
        return self.name

    def get_year(self):
        return self.year
    
    def add_episode(self, episode: Episode):
        if len(self.seasons) < episode.get_season():
            # init season list if doesn't exist
            self.seasons.insert(episode.get_season() - 1, []);

        self.seasons[episode.get_season() - 1].insert(episode.get_episode() - 1, episode.get_watched_at())
        pass

    def get_seasons(self):
        return self.seasons


shows = []

def get_show(name) -> Show:
    for show in shows:
        if show.get_name() == name:
            return show
    print("Created new show!", name)
    new_show = Show(name, 2022)
    shows.append(new_show)
    return new_show


# Function to convert a CSV to JSON
# Takes the file paths as arguments
def make_json(csvFilePath, jsonFilePath):

    # create a list
    data = []

    # Open a csv reader called DictReader
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)

        # Convert each row into a dictionary
        # and add it to data
        for row in csvReader:

            # print(row)
            show = get_show(row['grandparent_title'])
            print(show.get_name())

            episode = Episode(int(row['parent_media_index']), int(row['media_index']), epoch_to_string(int(row['stopped']) + 14400))
            print(episode.get_season(), episode.get_episode(), episode.get_watched_at());
            show.add_episode(episode)

            # # Assuming a column named 'No' to
            # # be the primary key
            # key = rows['rating_key']
            # data[key] = rows

    for show in shows:
        show_json = {'title': show.get_name()}
        show_json_seasons = []
        season_index = 1
        for season in show.get_seasons():
            season_json = {'number': season_index}
            season_index += 1

            season_json_episodes = []
            episode_index = 1
            for episode in season:
                season_json_episodes.append({'watched_at': episode, 'number': episode_index})
                episode_index += 1
                pass
            season_json['episodes'] = season_json_episodes

            show_json_seasons.append(season_json)

        show_json['seasons'] = show_json_seasons
        data.append(show_json)


# {
#     "title": "86: Eighty Six",
#     "year": 2021,
#     "seasons": [
#         {
#             "number": 1,
#             "episodes": [
#                 {
#                     "watched_at": "2021-04-24T15:45:43.000Z",
#                     "number": 2
#                 }
#             ]
#         }
#     ]
# }

    # Open a json writer, and use the json.dumps()
    # function to dump data
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps({
            "shows": data
        }, indent=4))

# Driver Code


# Decide the two file paths according to your
# computer system
csvFilePath = r'shows.csv'
jsonFilePath = r'shows.json'

# Call the make_json function
make_json(csvFilePath, jsonFilePath)

for s in shows:
    print(s.get_seasons())