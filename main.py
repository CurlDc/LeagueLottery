# coding=utf-8
import random
import csv
import json


class Person:

    def __init__(self, identifier, name, email, leagues_desired, pref_list=[], team_pref={}, league_coordinated=-1):
        self.identifier = identifier
        self.name = name
        self.email = email
        self.leagues_desired = leagues_desired
        self.pref_list = pref_list
        self.team_pref = team_pref  # dictionary keyed by league, value is team ID
        self.assignments = []
        self.waitlist_assignments = []
        self.league_coordinated = league_coordinated

    def assigned_leagues(self):
        return len(self.assignments)

    # If the league was not listed at all for this person this will return -1
    def league_preference(self, league):
        try:
            return self.pref_list.index(league)
        except ValueError:
            return -1

    def update_assignments(self, new_assignments, new_waitlist):
        self.assignments = new_assignments
        self.waitlist_assignments = new_waitlist

    def update_preferences(self, new_leagues_desired, new_pref_list, new_team_pref):
        self.leagues_desired += new_leagues_desired
        self.pref_list = new_pref_list
        self.team_pref = new_team_pref

    def clear_preferences(self):
        self.pref_list = []
        self.team_pref = {}


coordinator_placeholder = Person(0, "Coordinator", "Coordinator", 7)


class Entry:

    def __init__(self, entrant_list, team_id):
        self.entrants = entrant_list

    def size(self, global_league_limit=25):
        return len(self.eligible_entrants(global_league_limit))

    def eligible_entrants(self, global_league_limit=25):
        return [entrant for entrant in self.entrants if entrant.assigned_leagues() < entrant.leagues_desired
                and entrant.assigned_leagues() < global_league_limit]

    def assigned_leagues(self):
        if self.size() > 0:
            return sum([player.assigned_leagues() for player in self.entrants]) / float(self.size())
        return 0


class League:

    def __init__(self, identifier, name, capacity):
        self.identifier = identifier
        self.name = name
        self.capacity = capacity
        self.participant_list = [coordinator_placeholder]
        self.waitlist = []

    def spots_remaining(self):
        return self.capacity - len(self.participant_list)

    def add_to_league(self, registrant_list):
        if len(registrant_list) > self.spots_remaining():
            raise Exception

        self.participant_list.extend(registrant_list)

        for reg in registrant_list:
            reg.assignments.append(self.name)

    def add_to_waitlist(self, registrant_list):
        self.waitlist.extend(registrant_list)

        for reg in registrant_list:
            reg.waitlist_assignments.append(self.name)

    def add_coordinator(self, coordinator):
        self.participant_list.remove(coordinator_placeholder)
        self.add_to_league([coordinator])


def mk_int(s):
    s = s.strip()
    return int(s) if s else -1


def is_valid_league_choice(choice):
    return not (choice == '--None--' or choice == '')


# Loads registrant data from the given file and returns a registrant list
# League dict matches league names to ids
def load_registration_data(filename, league_dict):
    registrant_list = []
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row['First Name'] == 'EOF':
                break
            if row['League Lottery - # of Leagues Desired'] == '--No Lottery Leagues--' or row['League Lottery - # of Leagues Desired'] == '':
                continue
            identifier = row['Member ID']
            email = row['Email']
            name = ' '.join([row['First Name'], row['Last Name']])
            leagues_desired = mk_int(row['League Lottery - # of Leagues Desired'])
            pref_1_name = row['League Lottery - 1st Choice']
            pref_2_name = row['League Lottery - 2nd Choice']
            pref_3_name = row['League Lottery - 3rd Choice']
            pref_4_name = row['League Lottery - 4th Choice']
            pref_5_name = row['League Lottery - 5th Choice']
            pref_6_name = row['League Lottery - 6th Choice']
            pref_7_name = row['League Lottery - 7th Choice']
            pref_list = []
            team_pref = {}
            coordinator = -1
            if is_valid_league_choice(pref_1_name):
                pref_list.append(league_dict[pref_1_name])
                team_pref[league_dict[pref_1_name]] = mk_int(row['League Lottery - 1st Choice: Team'])
                if row['League Lottery - 1st Choice: Coordinator?'] == 'Y':
                    coordinator = league_dict[pref_1_name]
            """if row['Capital League'] == 'Y':
                pref_list.append(league_dict['Capital League'])
                team_pref[6] = -1
                leagues_desired += 1
            """
            if is_valid_league_choice(pref_2_name):
                pref_list.append(league_dict[pref_2_name])
                team_pref[league_dict[pref_2_name]] = mk_int(row['League Lottery - 2nd Choice: Team'])
                if row['League Lottery - 2nd Choice: Coordinator?'] == 'Y':
                    coordinator = league_dict[pref_2_name]
            if is_valid_league_choice(pref_3_name):
                pref_list.append(league_dict[pref_3_name])
                team_pref[league_dict[pref_3_name]] = mk_int(row['League Lottery - 3rd Choice: Team'])
            if is_valid_league_choice(pref_4_name):
                pref_list.append(league_dict[pref_4_name])
                team_pref[league_dict[pref_4_name]] = mk_int(row['League Lottery - 4th Choice: Team'])
            if is_valid_league_choice(pref_5_name):
                pref_list.append(league_dict[pref_5_name])
                team_pref[league_dict[pref_5_name]] = mk_int(row['League Lottery - 5th Choice: Team'])
            if is_valid_league_choice(pref_6_name):
                pref_list.append(league_dict[pref_6_name])
                team_pref[league_dict[pref_6_name]] = mk_int(row['League Lottery - 6th Choice: Team'])
            if is_valid_league_choice(pref_7_name):
                pref_list.append(league_dict[pref_7_name])
                team_pref[league_dict[pref_7_name]] = mk_int(row['League Lottery - 7th Choice: Team'])
            registrant_list.append(Person(identifier, name, email, leagues_desired, pref_list, team_pref, coordinator))

    return registrant_list


def load_registration_data_round2(filename, round1_results_filename, league_dict):
    registrant_dict = {}
    with open(round1_results_filename, mode='r') as json_file:
        json_obj = json.load(json_file)
        round1_player_list = json_obj['player_list']
        # Make sure to clear out first round preferences from everyone
        for player in round1_player_list:
            player_obj = Person(player['identifier'], player['name'], player['email'], player['leagues_desired'])
            player_obj.update_assignments(player['assignments'], player['waitlist_assignments'])
            player_obj.clear_preferences()
            registrant_dict[player['identifier']] = player_obj

    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row['First Name'] == 'EOF':
                break
            identifier = row['Member ID']
            email = row['Email']
            name = ' '.join([row['First Name'], row['Last Name']])
            leagues_desired = int(row['Round 2 Lottery - # of additional leagues desired'])
            pref_1_name = row['Round 2 Lottery - 1st Choice']
            pref_2_name = row['Round 2 Lottery - 2nd Choice']
            pref_list = []
            team_pref = {}
            if not pref_1_name == '--None--':
                pref_list.append(league_dict[pref_1_name])
                team_pref[league_dict[pref_1_name]] = int(row['Round 2 Lottery - 1st Choice: Team'])
            if not pref_2_name == '--None--':
                pref_list.append(league_dict[pref_2_name])
                team_pref[league_dict[pref_2_name]] = int(row['Round 2 Lottery - 2nd Choice: Team'])
            if identifier in registrant_dict.keys():
                registrant_obj = registrant_dict[identifier]
                registrant_obj.update_preferences(leagues_desired, pref_list, team_pref)
            else:
                registrant_dict[identifier] = Person(identifier, name, email, leagues_desired, pref_list, team_pref)

    return registrant_dict.values()


def run_league_registration(league_list, registrant_list, league_limit):
    registration_round = 0
    while any(len(reg.pref_list) > registration_round for reg in registrant_list):
        # This makes sure we process the most full league first
        # This matters in the first round for recycling players who got waitlisted
        available_spots_after_first_round = dict(zip(league_list,
                                                map(lambda league: league.capacity - len([reg for reg in registrant_list
                                                 if len(reg.pref_list) > registration_round
                                                 and reg.pref_list[registration_round] == league.identifier])
                                                                  , league_list)))
        sorted_league_list = sorted(league_list, key=lambda league: available_spots_after_first_round[league])
        for league in sorted_league_list:

            league_round_specific_player_list = [reg for reg in registrant_list
                                                 if len(reg.pref_list) > registration_round
                                                 and reg.pref_list[registration_round] == league.identifier]

            if not league_round_specific_player_list:  # When the league was not selected by anyone or is full
                continue
            # Process player list to have entry list with teams properly grouped
            teams = {}
            for player in league_round_specific_player_list:
                if player.league_coordinated == league.identifier:
                    league.add_coordinator(player)
                    continue
                if league.identifier in player.team_pref.keys():
                    player_team = player.team_pref[league.identifier]
                    if player_team not in teams.keys():
                        teams[player_team] = []
                    teams[player_team].append(player)

            entrant_list = []
            for team, teammates in teams.items():
                # Handle people who don't have a team
                if team == -1:
                    for single_entrant in teammates:
                        entrant_list.append(Entry([single_entrant], team))
                # When people have indicated a team group them together as one entry
                else:
                    entrant_list.append(Entry(teammates, team))
            # randomly order the interested participants
            random.shuffle(entrant_list)
            # Ensures players with less leagues are prioritized first
            entrant_list.sort(key=lambda entrant: entrant.assigned_leagues())

            capacity = league.spots_remaining()

            entrants_to_add = []
            entrants_to_waitlist = []
            for ent in entrant_list:
                # If the next team in the list fits in the league
                if capacity - len(entrants_to_add) >= ent.size(league_limit):
                    entrants_to_add.extend(ent.eligible_entrants(league_limit))
                # If the full team does not fit
                else:
                    entrants_to_waitlist.extend(ent.eligible_entrants(league_limit))

            league.add_to_league(entrants_to_add)
            if entrants_to_waitlist:
                league.add_to_waitlist(entrants_to_waitlist)
                registered_players = [reg for reg in registrant_list if
                                      reg.league_preference(league.identifier) > registration_round]
                random.shuffle(registered_players)
                registered_players.sort(key=lambda reg_player: reg_player.league_preference(league))

                league.add_to_waitlist(registered_players)
                if registration_round == 0:  # In the first round recycle waitlisted people into their second choice
                    registered_players.extend(entrants_to_waitlist)
                for player in registered_players:
                    player.pref_list.remove(league.identifier)

        registration_round += 1
        print ' '.join(["End of round", str(registration_round)])
        print_league_report(league_list)


def print_league_report(league_list):
    for league in league_list:
        print league.name
        print 'Available Spots:'
        print league.spots_remaining()
        print 'Roster:'
        for player in league.participant_list:
            print player.name
        print 'Waitlist:'
        for waiter in league.waitlist:
            print waiter.name


def print_league_email_report(league_list):
    for league in league_list:
        print league.name
        print 'Available Spots:'
        print league.spots_remaining()
        print 'Roster:'
        for player in league.participant_list:
            print player.email
        print 'Waitlist:'
        for waiter in league.waitlist:
            print waiter.email


def print_player_report(player_list):
    for player in player_list:
        print player.name
        print player.email
        print player.leagues_desired
        print player.pref_list
        print player.team_pref
        print player.assignments
        print player.waitlist_assignments


def save_data(filename, league_list, player_list):
    save_obj = {'league_list': league_list, 'player_list': player_list}
    with open(filename, 'w') as f:
        content = json.dumps(save_obj, default=lambda o: o.__dict__)
        f.write(content)


if __name__ == '__main__':
    league_dict = {"Sunday Pizza League": 0, "Monday Men's": 1, "Monday Women's(Front End)": 2,
                   "Monday Women's(Back End)": 3, "Tuesday Doubles": 4, "Tuesday Social": 5, "Capital League": 6,
                   "Thursday Open": 7, "TGIF Early": 8, "TGIF Late": 9}

    league_list = [League(0, "Sunday Pizza League", 72),
                   League(1, "Monday Men's", 40),
                   League(2, "Monday Women's(Front End)", 17),  # extra place since coordinator won't be replaced
                   League(3, "Monday Women's(Back End)", 17),  # extra place since no coordinator was named
                   League(4, "Tuesday Doubles", 20),
                   League(5, "Tuesday Social", 40),
                   League(6, "Capital League", 100),
                   League(7, "Thursday Open", 72),
                   League(8, "TGIF Early", 32),
                   League(9, "TGIF Late", 32)]

    player_list = load_registration_data(
        'C:/Users/Gilad/PycharmProjects/CurlingRegistration/venv/MemberRegistrationFall2023.csv',
        league_dict)
    print_player_report(player_list)
    print_league_report(league_list)

    run_league_registration(league_list, player_list, 7)
    save_data('dataExportFall2023.json', league_list, player_list)
    print "League registration completed"
    print_league_email_report(league_list)
    print_player_report(player_list)
    print_league_report(league_list)
