from riotwatcher import LolWatcher, ApiError

KEY = ""
lol_watcher = LolWatcher(KEY)

my_region = 'na1'

me = lol_watcher.summoner.by_name(my_region, 'Fr0gmin')
my_ranked_stats = lol_watcher.league.by_summoner(my_region, me['id'])
games = lol_watcher.match.matchlist_by_account(my_region, me["accountId"])
print(games)
