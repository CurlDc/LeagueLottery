# coding=utf-8
import argparse
import random
import csv
import json
import logging

logging.basicConfig(filename='LeagueLottery.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger()


class Member:
    """ All registion preferences, information, and league assignments for a club member
    """

    def __init__(self, id, name, email, num_leagues_desired, league_preferences):
        """Initialize a new Member object

        Args:
            identifier (int): member id for the member
            name (str): first and last name of the member
            email (str): email address of the member
            num_leagues_desired (int): the maximum number of leagues the member wants to register
            league_preferences (list(string)): the ordered list of preferences for leagues the member wants to register
        """
        self.id= id
        self.name = name
        self.email = email
        self.num_leagues_desired = num_leagues_desired
        self.league_preferences = league_preferences
        self.registered_leagues = []
        self.waitlisted_leagues = []

    def add_new_league_registration(self, new_assignment):
        """Inform the member they've been assigned to a league 

        Args:
            new_assignment (str): name of the league the member has been registered
        """
        self.registered_leagues.append(new_assignment)
        self.num_leagues_desired = self.num_leagues_desired - 1
        log.info(f'{self.name} registered for {new_assignment}')
        log.debug(f'{self.name} still wants {self.num_leagues_desired} leagues')

    def add_new_league_waitlist(self, new_assignment):
        """Inform the member they've been waitlisted for a league 

        Args:
            new_assignment (str): name of the league the member has been registered
        """
        self.waitlisted_leagues.append(new_assignment)
        log.info(f'{self.name} waitlisted for {new_assignment}')

    def write_registration_report(self, output_file_handle):
        if output_file_handle.closed:
            raise Exception('Output file handle is closed, cannot write registration report')
        output_file_handle.write(f'{self.name}\n')
        output_file_handle.write(f'{"=" * 80}\n')
        for l in self.registered_leagues:
            output_file_handle.write(f'{l}\n')
        output_file_handle.write('\n')

    def does_want_league(self, league_name, preference_num) -> bool:
        """determines if the member would be interested in registering for the league

        Args:
            league_name (str): name of league to check
            preference_num (int): which preference should we be checking

        Returns:
            bool: true if the member would be interested in registering
        """
        try:
            return self.num_leagues_desired > 0 and \
                self.league_preferences[preference_num] == league_name 
        except:
            return False


class League:
    """All the info for league registration
    """

    def __init__(self, name, capacity):
        self.name = name
        self.max_capacity = capacity
        self.capacity = capacity
        self.participant_list = []
        self.waitlist = []

    def has_spots_remaining(self) -> bool:
        return self.capacity - len(self.participant_list) > 0

    def add_to_league(self, registrant):
        if not self.has_spots_remaining() :
            msg  = f'{self.name} is full, cant add {registrant.name}'
            log.info(msg)
            raise Exception(msg)
        self.participant_list.append(registrant.name)
        log.debug(f'Adding {registrant.name} to league {self.name}')
        registrant.add_new_league_registration(self.name)

    def add_to_waitlist(self, registrant):
        self.waitlist.append(registrant.name)
        log.debug(f'Adding {registrant.name} to league {self.name}')
        registrant.add_new_league_waitlist(self.name)

    def write_registration_report(self, output_file_handle):
        if output_file_handle.closed:
            raise Exception('Output file handle is closed, cannot write registration report')
        output_file_handle.write(f'{self.name}\n')
        output_file_handle.write(f'{"=" * 80}\n')
        output_file_handle.write(f'Max Capacity: {self.max_capacity}\n')
        output_file_handle.write(f'Current Registration: {len(self.participant_list)}\n')
        output_file_handle.write(f'Waitlist Size: {len(self.waitlist)}\n')
        output_file_handle.write(f'{"-" * 80}\n')
        output_file_handle.write(f'Roster:\n')
        for m in self.participant_list:
            output_file_handle.write(f'\t{m}\n')
        output_file_handle.write(f'{"-" * 80}\n')
        output_file_handle.write(f'Waitlist:\n')
        for m in self.waitlist:
            output_file_handle.write(f'\t{m}\n')
        output_file_handle.write('\n')


def load_registration_data(filename) -> dict:
    """Loads the member roster and the registration preferences from the Curling Manager export

    Args:
        filename (str): Path to the CM exported CSV file

    Returns:
        dict: All the members' registration details, keyed off of member id
    """
    def has_league_preference(choice):
        return not (choice == '--None--' or choice == '')

    def wants_leagues(choice):
        return not (choice == '--No Lottery Leagues--' or choice == '')

    roster = {}

    #CSV Columns
    first_name = 'First Name'
    last_name = 'Last Name'
    member_id = 'Member ID'
    email = 'Email'
    num_leagues_requested = 'League Lottery - Max # of Leagues Desired'
    lottery_choices = ['League Lottery - 1st Choice',
                       'League Lottery - 2nd Choice',
                       'League Lottery - 3rd Choice',
                       'League Lottery - 4th Choice',
                       'League Lottery - 5th Choice',
                       'League Lottery - 6th Choice',
                       'League Lottery - 7th Choice'
                       ]

    with open(filename, mode='r') as handle:
        csv_reader = csv.DictReader(handle)
        for row in csv_reader:
            if not wants_leagues(row[num_leagues_requested]):
                log.info(f"{row[first_name]} {row[last_name]} doesn't want any leagues")
                continue
            leagues_desired = int(row['League Lottery - Max # of Leagues Desired'].strip())
            pref_list = []
            for p in [row[l] for l in lottery_choices if has_league_preference(row[l])]:
                pref_list.append(p)
            log.debug(f"{row[first_name]} {row[last_name]} wants {leagues_desired} from {pref_list}")
            roster[int(row[member_id])] = Member(int(row[member_id]),
                                            ' '.join([row[first_name], row[last_name]]),
                                            row[email],
                                            leagues_desired, 
                                            pref_list)
    return roster


def initialize_leagues(coordinator_csv, roster) -> dict:
    """Uses the CSV provided by member services to register the coordinators in the appropriate leagues. 
    
    Note currently only the first coordinator is guarenteed a spot.

    Args:
        coordinator_csv (str): Path to file containing coordinator info
        roster (dict(Member)): All members registering for the season, keyed off of the member id

    Returns:
        a dictionary containing the leagues with the appropriate number of teams and coordinators, keyed off of the league names.
    """
    # Expected columns in the CSV
    # the ids are the Member IDs Curling Manager provides
    league_name = 'League'
    num_teams_col = 'Max teams'
    coordinator_1_id = 'Coordinator #1'
    coordinator_2_id = 'Coordinator #2'
    coordinator_3_id = 'Coordinator #3'

    leagues = {}

    with open(coordinator_csv, 'r') as file_handle:
        csv_reader = csv.DictReader(file_handle)
        for row in csv_reader:
            if row['League'] == 'EOF':
                break

            current_league = row[league_name].strip()
            league_capacity = int(row[num_teams_col].strip()) * 4
            coordinator_id = int(row[coordinator_1_id].strip())

            new_league = League(current_league, league_capacity)
            log.info(f'Adding {roster[coordinator_id].name} as coordinator for {current_league}')
            new_league.add_to_league(roster[coordinator_id])
            # Don't bother checking for the exception, the league is empty so unless we have bad data it shouldn't fail here

            leagues[current_league] = new_league
    return leagues


def run_league_registration(roster, leagues, max_num_league_choices=7):
    """Run the lottery and register members for leagues

    Args:
        roster (dict(int:Member)): all the members, keyed by member id
        leagues (dict(str:League)): all the leagues, keyed by name
        max_num_league_choices (int) : The maximum number of leage preferences a member can have. Defaults to 7
    """
    for r in range(7):
        for league in leagues.values():
            log.debug(f'Running selections for {r} preference for {league.name}')
            if not league.has_spots_remaining():
                log.debug(f'{league.name} is full, moving to next league')
                continue
            candidates = []
            for member in roster.values():
                if member.does_want_league(league.name, r):
                    log.debug(f'{member.name} will be a candidate for {league.name}')
                    candidates.append(member)

            if len(candidates) <= league.capacity:
                log.info(f'Adding all {len(candidates)} to {league.name} league')
                winners = candidates
            else:
                log.info(f'Selecting up to {league.capacity} new candidates for {league.name}')
                winners = random.sample(candidates, k=league.capacity)

            for winner in winners:
                log.debug(f'Adding {winner.name} to {league.name}')
                try:
                    league.add_to_league(winner)
                except:
                    log.warning(f'{league.name} is full, adding {winner.name} to the waitlist')
                    #this shouldn't really happen since we're using remaining capacity to select
                    league.add_to_waitlist(winner)
            for unfortunate_member in [x for x in candidates if x not in winners]:
                log.debug(f'{league.name} is full, adding {winner.name} to the waitlist')
                league.add_to_waitlist(unfortunate_member)
            
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help='Input CSV with registrants', required=True)
    parser.add_argument('-c', '--coordinator-file', help='Input CSV with approved coordinator data', required=True)
    parser.add_argument('-o', '--output-file', help='Path to write lottery results', required=True)
    args = parser.parse_args()

    log.debug(f'Loading registration data from {args.input_file}')
    roster = load_registration_data(args.input_file)

    log.debug(f'Loading league initialization data from {args.coordinator_file}')
    leagues = initialize_leagues(args.coordinator_file, roster)

    log.debug(f'Running lottery')
    run_league_registration(roster, leagues)

    print("League registration completed")

    with open(args.output_file, 'w') as output_handle:
        output_handle.write('Registration Results\n')
        output_handle.write(f'{"*" * 80}\n')
        for member in roster.values():
            member.write_registration_report(output_handle)
            output_handle.write('\n\n')

        output_handle.write(f'{"*" * 80}\n')
        output_handle.write(f'{"*" * 80}\n')
        output_handle.write(f'{"*" * 80}\n')

        output_handle.write('\n\n')
        output_handle.write('League Rosters:\n')
        output_handle.write(f'{"*" * 80}\n')
        for league in leagues.values():
            league.write_registration_report(output_handle)
            output_handle.write('\n\n')
