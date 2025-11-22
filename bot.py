# <IMPORTS HERE>
import random
from typing import Optional, Tuple # probably important
# </IMPORTS HERE>

# <DO NOT MODIFY>
from helpers import *

class Pot:
    value: int
    players: list[str]


class GameState:
    index_to_action: int
    index_of_small_blind: int
    players: list[str]
    player_cards: list[str]
    held_money: list[int]
    bet_money: list[int]
    community_cards: list[str]
    pots: list[Pot]
    small_blind: int
    big_blind: int
# </DO NOT MODIFY>


# len(pots) > 1 iff there's a side pot (all in + betting after someone's all in)

# class GameState:
#     index_to_action: int # your index, for example, bet_money[index_to_action] is your bot's current betting amount
#     index_of_small_blind: int
#     players: list[str] # list of bots' id, ordered according to their seats
#     player_cards: list[str] # list of your cards
#     held_money: list[int]
#     bet_money: list[int]  # -1 for fold, 0 for check/hasn't bet
#     community_cards: list[str]
#     pots: list[Pot] # a list of dicts that contain "value" and "players". "value" is the amount in that pot, "players" are the eligible players to win that pot.
#     small_blind: int
#     big_blind: int

"""
{
    "index_to_action": 2,
    "index_of_small_blind": 0,
    "players": ["team_id0", "team_id1", "team_id2"],
    "player_cards": ["2s", "7s"],
    "held_money": [100, 200, 300],
    "bet_money": [20, -1, 0],
    "community_cards": ["ac", "2h", "2d"],
    "pots": [{ "value": 50, "players": ["team_id0", "team_id2"] }],
    "small_blind": 5,
    "big_blind": 10
}

"""



""" Store any persistent data for your bot in this class """
class Memory:
    # bot_vs => list of dicts
    # each dict has number of 'actions' seen and the 'score' for each bot

    # track each bot's:
    # key: str - id of the bot
    # value: int - int id in the bot_stats list thing
    looseness = {}

    # track:
    # [0]: str -  bot id
    # [1]: int - number of hands tracked
    # [2]: int - "score". (+1 for fold, -1 for putting money in, -1.2 for a raise, -2 for all in)
    stats = []

    bluff = False # built in bluff mechanic
    # this is deprecated.
    # we are not bluffing

    raise_factor = 2.5
    
    seen_action_once = 0 


    def __init__(self):
        self.looseness = {}
        self.bluff = False 
        self.seen_action_once = 0
        self.raise_factor = 2.5
        self.stats = []

    # action is either +1 (fold), -1 (call), -1.2 for a raise, -2 for all in
    def add_action(self, player_id, hands_incr, action):
        if player_id in self.looseness:
            # nice!
            # player is already logged.
            # find their ind in stats and add to it
            for i, ls in enumerate(self.stats):
                if ls[0] == player_id:
                    self.stats[i][1] += hands_incr
                    self.stats[i][2] += action

                    self.looseness[player_id] = self.stats[i][2] / self.stats[i][1]
                    return 
                
                continue
        
        # not tracked.
        # hands_incr should be 1 here but i digress.
        self.stats.append([player_id, hands_incr, action])
        self.looseness[player_id] = action/(hands_incr + 1)
        return
 
    def get_looseness(self, player_id):
        if player_id in self.looseness:
            return self.looseness[player_id]
        
        return 0


""" Make a betting decision for the current turn.

    This function is called every time your bot needs to make a bet.

    Args:
        state (GameState): The current state of the game.
        memory (Memory | None): Your bot's memory from the previous turn, or None if this is the first turn.

    Returns:
        tuple[int, Memory | None]: A tuple containing:
            bet_amount: int - The amount you want to bet (-1 to fold, 0 to check, or any positive integer to raise)
            memory: Memory | None - Your bot's updated memory to be passed to the next turn
"""
# DO NOT MODIFY THE FUNCTION SIGNATURE
def bet(state: GameState, memory: Memory | None=None) -> tuple[int, Memory | None]:

    if memory is None:
        memory = Memory()

    # TODO: turn this off.
    debug = 0 
    if debug:
        ## debug stuffs
        # write the full game state to the output log
        to_write = [f'index_to_action: {state.index_to_action}', f'index_of_small_blind: {state.index_of_small_blind}', f'players: {state.players}', f'player_cards: {state.player_cards}', f'held_money: {state.held_money}', f'bet_money: {state.bet_money}', f'community_cards {state.community_cards}', 'pots: [{ "value": ' + f'{state.pots[0].value}' + ', "players": ' + f'{state.pots[0].players}' + '}]', f'small_blind: {state.small_blind}', f'big_blind: {state.big_blind}']

        with open('game_state.txt', 'a') as f:
            f.write('*********'*3 + '\n')
            f.write('current gamestate:\n{\n')
            for i in to_write:
                f.write(f'\t{i}\n')

            f.write('}\n')
            
            # write memory
            if memory is None:
                pass 
            else:

                f.write('\n')
                f.write(f'memory type: {type(memory)}\n')
                f.write(f'memory: {memory}\n')
                f.write(f'memory mappings: {memory.looseness}\n')
                f.write(f'all stats in memory: {memory.stats}\n')
                f.write('\n')

            f.write('========='*3 + '\n')
            f.write('\n')


    raise_factor = memory.raise_factor

    # preflop tables!
    # heads up jam  
    # removed some hands here for fun
    two_jam_table = {
        "aa": 1, "aks": 1, "aqs": 1, "ajs": 1, "ats": 1, "a9s": 1, "a8s": 1, "a7s": 1, "a6s": 1, "a5s": 1, "a4s": 1, "a3s": 1, "a2s": 1, 
        "ako": 1, "kk": 1, "kqs": 1, "kjs": 1, "kts": 1, "k9s": 1, "k8s": 1, "k7s": 1, "k6s": 1, "k5s": 1, "k4s": 1, "k3s": 1, "k2s": 1, 
        "aqo": 1, "kqo": 1, "qq": 1, "qjs": 1, "qts": 1, "q9s": 1, "q8s": 1, "q7s": 1, "q6s": 0, "q5s": 1, "q4s": 1, "q3s": 1, "q2s": 1, 
        "ajo": 1, "kjo": 1, "qjo": 1, "jj": 1, "jts": 1, "j9s": 1, "j8s": 1, "j7s": 1, "j6s": 1, "j5s": 1, "j4s": 1, "j3s": 1, "j2s": 0, 
        "ato": 1, "kto": 1, "qto": 1, "jto": 1, "tt": 1, "t9s": 1, "t8s": 1, "t7s": 1, "t6s": 1, "t5s": 1, "t4s": 0, "t3s": 1, "t2s": 0, 
        "a9o": 1, "k9o": 1, "q9o": 1, "j9o": 1, "t9o": 1, "99": 1, "98s": 1, "97s": 1, "96s": 1, "95s": 0, "94s": 0, "93s": 0, "92s": 0, 
        "a8o": 1, "k8o": 1, "q8o": 1, "j8o": 1, "t8o": 1, "98o": 1, "88": 1, "87s": 1, "86s": 1, "85s": 0, "84s": 0, "83s": 0, "82s": 0, 
        "a7o": 1, "k7o": 1, "q7o": 1, "j7o": 1, "t7o": 1, "97o": 1, "87o": 1, "77": 1, "76s": 1, "75s": 0, "74s": 0, "73s": 0, "72s": 0, 
        "a6o": 1, "k6o": 1, "q6o": 1, "j6o": 0, "t6o": 0, "96o": 0, "86o": 0, "76o": 1, "66": 1, "65s": 1, "64s": 0, "63s": 0, "62s": 0, 
        "a5o": 1, "k5o": 1, "q5o": 0, "j5o": 0, "t5o": 0, "95o": 0, "85o": 0, "75o": 0, "65o": 0, "55": 1, "54s": 1, "53s": 0, "52s": 0, 
        "a4o": 1, "k4o": 1, "q4o": 0, "j4o": 1, "t4o": 0, "94o": 0, "84o": 0, "74o": 0, "64o": 0, "54o": 0, "44": 1, "43s": 0, "42s": 0, 
        "a3o": 1, "k3o": 0, "q3o": 0, "j3o": 0, "t3o": 0, "93o": 0, "83o": 0, "73o": 0, "63o": 0, "53o": 0, "43o": 0, "33": 1, "32s": 0, 
        "a2o": 1, "k2o": 1, "q2o": 0, "j2o": 0, "t2o": 0, "92o": 0, "82o": 0, "72o": 0, "62o": 0, "52o": 0, "42o": 0, "32o": 0, "22": 1
    }

    # made up numbers based on vibes and shit
    # i dont even know at some level.
    five_table = {
        "aa": 1135, "aks": 120, "aqs": 100, "ajs": 90, "ats": 65, "a9s": 40, "a8s": 35, "a7s": 22, "a6s": 12, "a5s": 15, "a4s": 12, "a3s": 11, "a2s": 10, 
        "ako": 100, "kk": 963,  "kqs": 60,  "kjs": 40, "kts": 24, "k9s": 14, "k8s": 8,  "k7s": 7,  "k6s": 6, "k5s": 5, "k4s": 5, "k3s": 5, "k2s": 5, 
        "aqo": 90,  "kqo": 35,  "qq": 500,  "qjs": 35, "qts": 25, "q9s": 14, "q8s": 8,  "q7s": 5,  "q6s": 4, "q5s": 3, "q4s": 3, "q3s": 3, "q2s": 3, 
        "ajo": 70,  "kjo": 20,  "qjo": 15,  "jj": 120, "jts": 20, "j9s": 15, "j8s": 8,  "j7s": 6,  "j6s": 2, "j5s": 2, "j4s": 1, "j3s": 0, "j2s": 0, 
        "ato": 40,  "kto": 13,  "qto": 10,  "jto": 15, "tt": 100, "t9s": 15, "t8s": 10, "t7s": 6,  "t6s": 2, "t5s": 0, "t4s": 0, "t3s": 0, "t2s": 0, 
        "a9o": 20,  "k9o": 7,   "q9o": 6,   "j9o": 10, "t9o": 10, "99": 90,  "98s": 10, "97s": 6,  "96s": 3, "95s": 0, "94s": 0, "93s": 0, "92s": 0, 
        "a8o": 10,  "k8o": 4,   "q8o": 4,   "j8o": 5,  "t8o": 6,  "98o": 7,  "88": 70,  "87s": 5,  "86s": 2, "85s": 0, "84s": 0, "83s": 0, "82s": 0, 
        "a7o": 9,   "k7o": 3,   "q7o": 2,   "j7o": 3,  "t7o": 2,  "97o": 5,  "87o": 4,  "77": 55,  "76s": 3, "75s": 0, "74s": 0, "73s": 0, "72s": -1, 
        "a6o": 8,   "k6o": 2,   "q6o": 0,   "j6o": 0,  "t6o": 0,  "96o": 1,  "86o": 1,  "76o": 0,  "66": 40, "65s": 2, "64s": 0, "63s": 0, "62s": 0, 
        "a5o": 9,   "k5o": 2,   "q5o": 0,   "j5o": 0,  "t5o": 0,  "95o": 0,  "85o": 0,  "75o": 0,  "65o": 0, "55": 32, "54s": 0, "53s": 0, "52s": 0, 
        "a4o": 8,   "k4o": 2,   "q4o": 1,   "j4o": 1,  "t4o": 0,  "94o": 0,  "84o": 0,  "74o": 0,  "64o": 0, "54o": 0, "44": 30, "43s": 0, "42s": 0, 
        "a3o": 7,   "k3o": 0,   "q3o": 0,   "j3o": 0,  "t3o": 0,  "93o": 0,  "83o": 0,  "73o": 0,  "63o": 0, "53o": 0, "43o": 0, "33": 25, "32s": 0, 
        "a2o": 6,   "k2o": 0,   "q2o": 1,   "j2o": 0,  "t2o": 0,  "92o": 0,  "82o": 0,  "72o": 0,  "62o": 0, "52o": 0, "42o": 0, "32o": 0, "22": 20,
    }

    my_bet = state.bet_money[state.index_to_action]
    chips = state.held_money[state.index_to_action]
    num_players = len(state.players)


    table_q = (chips + my_bet) * len(state.players) / (sum(state.held_money) + sum(state.bet_money)) # only useful preflop
    # q > 1 => above average stack size at the table.

    m_value = chips / (state.small_blind + state.big_blind)
    eff_m = m_value * (num_players / 9) # note that eff_m will always be nerfed slightly


    # game startup memory tweaks
    if my_bet == 0 and len(state.community_cards) == 0:
        memory.seen_action_once = 0
        memory.bluff = False
    
    


    ######################################
    # heads up 
    # TODO: change this back to 2.
    if num_players == 2:
        # heads up!
        # dont even worry about memory.

        current_hand = convert_hand(state.player_cards)

        if two_jam_table[current_hand]:
            # all in
            # return (chips, memory)
            
            # only put necessary chips in
            return (min(state.bet_money[1 - state.index_to_action] + state.held_money[1 - state.index_to_action] - state.bet_money[state.index_to_action], chips), memory)
        
        return (-1, memory)

    ###################################### </heads up>
    
    # calculate table looseness (average)
    # pull values from memory for this!
    table_looseness = 0
    for _player in state.players:
        table_looseness += memory.get_looseness(_player)

    table_looseness /= num_players

    ######################################
    # pre-flop action
    
    # update memory to see who's playing / who's not
    # for now only gather data when its pre-flop and i have no chips in the pot (besides blinds)

    # first round preflop.
    if not memory.seen_action_once:
        memory.seen_action_once = 1

        _ind = (state.index_of_small_blind + 2) % num_players
        _bet = state.big_blind
        while _ind % num_players != state.index_to_action:
            # fold: +1. call: -1. raise: -1.2. all in: -2
            _id = state.players[_ind]

            if state.held_money[_ind] == 0:
                memory.add_action(_id, 1, -2)
                _ind += 1
                continue 
            
            if state.bet_money[_ind] > _bet:
                # raise.
                memory.add_action(_id, 1, -1.2)
                _bet = state.bet_money[_ind]

            elif state.bet_money[_ind] == _bet:
                memory.add_action(_id, 1, -1)
            elif state.bet_money[_ind] < _bet:
                memory.add_action(_id, 1, 1) # fold. has to be less than (<) cuz small blind might fold even tho chips in.

            _ind = (_ind + 1) % num_players
            continue
    elif memory.seen_action_once == 1: # 2nd time its back to me preflop
        memory.seen_action_once = 2

        _bet = my_bet # should be minimum. go from there.
        
        for _ind in range(state.index_to_action + 1, state.index_to_action + num_players):
            _ind = _ind % num_players


            _id = state.players[_ind]

            if state.held_money[_ind] == 0 and state.bet_money[_ind] > _bet - 0.0001:
                # slap him with a -1.2 since already -1 to call 
                memory.add_action(_id, 0, -1.2)
                _bet = state.bet_money[_ind]
                continue 
            
            if state.bet_money[_ind] > _bet:
                # raise.
                memory.add_action(_id, 0, -0.5) # honestly idek
                _bet = state.bet_money[_ind]

            elif state.bet_money[_ind] < _bet:
                if state.bet_money[_ind] < 0.1:
                    # already tracked the fold from last time.
                    continue 
                
                # -1 + 0.5 = -0.5 => fold, but he still limped/whateverd

                memory.add_action(_id, 0, 0.5) # fold. has to be less than (<) cuz small blind might fold even tho chips in.
            
            # == case we'll call vpip still.
            
            continue 

    # 3rd+ time preflop we dont even worry about it.
    


    # preflop action decider
    # f(my stack, number of players, my position, table looseness, hand equity)
    if not len(state.community_cards):
        current_hand = convert_hand(state.player_cards)

        # count number of 3/4/5+ bets (note: code not entirely accurate here)
        bet_count = len(set({a for a in state.bet_money if a not in [0, -1, state.small_blind, state.big_blind]})) + 1

        if eff_m <= 5 or m_value < 8 or (table_q < 0.8 and m_value < 11):
            # find a spot to jam

            table_size_const = 2
            button_const = 2
            looseness_const = 3

            score = 0

            # add to the score if theres been 3-bets/4-bets
            if bet_count > 4:
                # get out unless you have 99+ or AK/AQ
                if current_hand in ['aa', 'kk', 'qq', 'jj', 'tt', '99', 'aks', 'aqs']:
                    return (chips, memory)
                
                return (-1, memory)

            if bet_count == 4:
                # jam if you have a good hand lol
                score += 20
            
            if bet_count == 3:
                score += 5

            # how loose is the table? (-2, 1)
            score += table_looseness*looseness_const
            
            # see how low stacked i am
            # low stacked (6-10) means score should go up since i should jam on "better" hands.
            if eff_m > 5.9:
                score += 4


            # see how many people are in the hand
            # less people => more folds
            score += table_size_const*(num_players - 5)

            # see my position for action
            # on the button = better to jam
            # so ill loosen it up by a tad on the button / button - 1
            if state.index_of_small_blind == ((state.index_to_action + 1) % num_players):
                score -= button_const

            if state.index_of_small_blind == ((state.index_to_action + 2) % num_players):
                score -= button_const / 2

            
            # compare with hand equity
            if five_table[current_hand] > max(0, score):
                # jam.
                return (chips, memory)
            
            # fold.
            return (-1, memory)

        # ok well do the same equity calculations but see what kinda bet we got going.
        if (m_value > 36 and table_q > 0.8) or table_q > 1.34:
            # eff ~ 54bb if 2*sb = bb
            # go wager on hands that dont have preflop raises and stuff

            position_const = 2
            looseness_const = 3

            score = 0
            
            # look at position; am i on the button / button -1? if so play a little loose.
            if state.index_of_small_blind == ((state.index_to_action + 1) % num_players) or state.index_of_small_blind == ((state.index_to_action + 2) % num_players):
                # play anything less than 3bb
                if 3*state.big_blind + 0.1 > max(state.bet_money):
                    # call, or raise if the price is right
                    if five_table[current_hand] > 15 and current_hand not in ['22', '33', '44', '55', '66']:
                        # raise to 2x.
                        return (int(max(state.bet_money)*raise_factor - my_bet), memory)
                    
                    # call.
                    return (max(state.bet_money) - my_bet, memory)
                
                # only play if score is good enough, e.g. pass for now

                score -= position_const # we have position

            # position filter.
            if state.index_to_action == ((state.index_of_small_blind + 1) % num_players) or (state.index_to_action == ((state.index_of_small_blind + 1) % num_players) and num_players > 5):
                # early position :(
                score += position_const
            

            # add in bet sizings
            if bet_count > 2 or max(state.bet_money)*6 > chips + my_bet - 0.1:
                score += 20
            if bet_count > 3 or max(state.bet_money)*3 > chips + my_bet - 0.1:
                score += 50
            if bet_count > 4:
                score += 200

            # looseness
            score += looseness_const*table_looseness

            # are we priced in?
            if (max(state.bet_money) - my_bet) > my_bet*2.5:
                # nope
                pass
            elif (max(state.bet_money) - my_bet) > my_bet*1.4: # 2.5x or 3x raise.
                score -= 4
            elif (max(state.bet_money) - my_bet) > my_bet*0.5:
                score -= 10
            else:
                # priced in call
                return (min(chips, max(state.bet_money) - my_bet), memory)

            if five_table[current_hand] - max(10, score*0.2) > max(0, score):
                # raise.
                return (int(min(max(state.bet_money)*raise_factor - my_bet, chips)), memory)
            
            # call.
            return (min(chips, max(state.bet_money) - my_bet), memory)

                
        hand_score = five_table[current_hand]
        if 3*state.big_blind + 0.1 > max(state.bet_money):
            # call/raise.
            if hand_score > 35:
                return (min(int(max(state.bet_money)*raise_factor) - my_bet, chips), memory)
            if hand_score > 7:
                return (min(chips, max(state.bet_money) - my_bet), memory)
            return (-1, memory)
            
        # only play if score is good enough, e.g. pass for now
        if hand_score > 42:
            return (int(min(chips, max(state.bet_money)*raise_factor - my_bet)), memory)
        
        # call if good hand / priced in for over 1/3.5 already
        if hand_score > 19 or (hand_score > 10 and max(state.bet_money)*3.5 > chips + my_bet - 0.1):
            # call and see the flop.
            return (min(chips, max(state.bet_money) - my_bet), memory)
        
        # fold.
        return (-1, memory)
    ###################################### </preflop>

   
    ###################################### 
    # flop 
    # check-raising is too hard to implement, don't do it.
    # bluffing is also too hard, don't do it
    
    # TODO (later lolz): factor stack size into account before doing anything

    # nothing, low/mid pair, high pair, 2 pair, set, flush draw, straight draw (flush, straight, full house, quads)
    if len(state.community_cards) == 3:
        board_eval = evaluate_board(state.player_cards, state.community_cards)

        # NOTE: board could be wet and my bot wouldnt know
        # e.g. QsQc on a 5h6h7h board would not be great but my bot wouldnt know and play it like a regular overpair

        # NOTE: this bot also cannot realize that it has two things (e.g. top pair + straight draw) - it will only see the straight draw and play off that.

        # NOTE: this is also assuming post-flop heads up play (but its still ok if not)
        # NOTE: this bot is not good in multi-way side pot flops

        
        pot = 0 
        for _p in state.pots:
            pot += _p.value
        
        if my_bet == 0 and max(state.bet_money) < pot // 10:
            if board_eval > 10 and board_eval % 10:
                r = random.randint(1, 10) # 30% all in, 20% 3/4ths, 50% pot

                if r < 4:
                    return (chips, memory) # all in
                
                if r < 6:
                    return (min(chips, 3 * pot // 4), memory)
                
                return (min(chips, pot), memory)
            
            if board_eval == 40:
                # pot size bet basically
                return (min(pot, chips), memory)
            
            if board_eval == 30:
                # half pot bet, disguised as somtehing else lol
                return (min(pot // 2, chips), memory)
            
            if board_eval == 20:
                # 8 outs ~ 32% ish
                # pot size bet is still ok
                # bet 3/4ths
                return (min(chips, int(3 * pot // 4)), memory)
            
            if board_eval == 10:
                # 4 outs ~ 16% ish
                # pot size is mid so we'll check
                return (min(chips, max(state.bet_money)), memory)
            
            if not board_eval:
                return (-1, memory)
            
            # check the nothing over
            if board_eval == 1:
                return (min(chips, max(state.bet_money)), memory)
            
            # sometimes bluff
            if board_eval == 2:
                r = random.randint(1, 6)

                if r == 1:
                    return (min(chips, pot // 2), memory)
                
                return (min(chips, max(state.bet_money)), memory)
            
            # sometimes bet on the high pair 
            if board_eval == 4:
                r = random.randint(1, 10)
                if r > 3:
                    return (min(chips, pot // 2), memory)
                
                return (min(chips, max(state.bet_money)), memory)

            # sometimes bet on the middle pair
            if board_eval == 3:
                r = random.randint(1, 10)
                if r > 6:
                    return (min(chips, pot // 2), memory)
                
                return (min(chips, max(state.bet_money)), memory)

            # almsot kinda basically the nuts
            # bet or dont bet sometimes
            if board_eval == 9 or board_eval == 7 or board_eval == 6:
                r = random.randint(1, 10)
                if r < 4:
                    return (min(chips, max(state.bet_money)), memory)

                return (min(chips, pot), memory)
            
            # 3/4ths with the low flush
            if board_eval == 8:
                return (min(chips, int(3 * pot // 4)), memory)
            
            # 1/2 with the 2 pair cuz why not
            if board_eval == 5:
                return (min(chips, pot // 2), memory)
            
            return (min(chips, max(state.bet_money)), memory)

        if my_bet == 0:
            to_call = max(state.bet_money)
            # yikes he bet into me.
            if board_eval > 10 and board_eval % 10:
                # jam.
                return (chips, memory)

            # fold bad stuff (ace high, med pair)
            if board_eval < 4:
                return (-1, memory)
            
            # call any flush draws as long as its equity
            if board_eval == 30 or board_eval == 40 or board_eval == 20 and pot > to_call:
                return (min(chips, to_call), memory)
            
            if board_eval == 10:
                return (-1, memory)
            
            if board_eval == 8 and to_call > 3 * pot // 4 - 2:
                return (-1, memory) # alr bruh
            
            if board_eval in [9, 8, 7, 6]: # basically the nuts (besides low flush), jam on them
                return (chips, memory)
            
            if board_eval == 5 and to_call > pot:
                return (-1, memory)
            
            if board_eval == 5 and is_pair(state.community_cards):
                # hmm this is a real sweat
                # lets just leave it up to odds lowkey
                r = random.randint(1, 5)
                if r < 3:
                    return (min(chips, to_call), memory)
                
                return (-1, memory)
            
            if board_eval == 5:
                return (min(chips, to_call), memory)

            if board_eval == 4 and to_call > 3 * pot // 4 + 0.1:
                return (-1, memory)
            
            if board_eval == 4:
                # lets just call top pair since he might be barreling with nothing
                # some of the time
                r = random.randint(1, 10)
                if r < 4:
                    return (-1, memory)
            
                return (min(chips, to_call), memory)
        
            # fold.?????
            return (-1, memory)
            
        
        ################### copy over code from previous
        # so now hes basically reraised me
        # logic is p similar to previous times and stuff

        pot += max(state.bet_money) + my_bet # for equity reasons
        to_call = max(state.bet_money) - my_bet
        # yikes he bet into me.
        if board_eval > 10 and board_eval % 10:
            # jam.
            return (chips, memory)

        # fold bad stuff (ace high, med pair)
        if board_eval < 5:
            return (-1, memory)
        
        # call any strong draws as long as its equity
        if board_eval == 40 or board_eval == 20 and pot > to_call:
            return (min(chips, to_call), memory)
        
        if board_eval == 10 or board_eval == 30:
            return (-1, memory)
        
        if board_eval == 8 and to_call > 0.4*pot:
            return (-1, memory) # alr bruh
        
        if board_eval in [9, 8, 7, 6]: # basically the nuts (besides low flush), jam on them
            return (chips, memory)
        
        if board_eval == 5 and to_call > 0.35*pot:
            return (-1, memory)
        
        if board_eval == 5 and is_pair(state.community_cards):
            return (-1, memory)
        
        if board_eval == 5:
            return (min(chips, to_call), memory)

    
        # fold.?????
        return (-1, memory)
    

    ###################################### </flop>


    ###################################### 
    # turn
    # basically play the nuts or anything else if value.
    if len(state.community_cards) == 4:

        

        # NOTE: literally the exact same issues as before are still present

        
        pot = 0 
        for _p in state.pots:
            pot += _p.value
        
        board_eval = evaluate_board(state.player_cards, state.community_cards)

        ############### opening bet on the turn- only bet if you're willing to jam!

        if my_bet == 0 and max(state.bet_money) < 1:
            # check everything but the nuts, and bet pot size with the nuts.
            # me tired and want the sleepy so this will be simple.

            if board_eval in [9, 7, 6, 11, 12, 13]:
                # these seem to be the nuts.
                return (min(chips, pot), memory)

            return (0, memory)
        
        if my_bet == 0:
            to_call = max(state.bet_money)
            # i have the option to call some things.
            # jam the nuts, call things if they're equity enough.
            if board_eval in [9, 7, 6, 11, 12, 13]:
                # these seem to be the nuts.
                return (chips, memory)
            
            if board_eval == 40 or board_eval == 20 or board_eval == 5 and 0.25*pot > to_call:
                return (to_call, memory)
            
            if board_eval == 4:
                if state.player_cards[0][0] in ['a', 'k'] or state.player_cards[1][0] in ['a', 'k']:
                    # call if the price is right
                    if 0.35*pot > to_call:
                        return (min(chips, to_call), memory)
                    
                    if 0.65*pot > to_call:
                        r = random.randint(1, 3)
                        if r == 1:
                            return (min(chips, to_call), memory)

            return (-1, memory)
    
        if my_bet > 0:
            # jam.
            return (chips, memory)
        
        # ehrm
        return (0, memory) # worst that can happen is an invalid => auto fold.

    ###################################### </turn>
    

    ###################################### 
    # river
    # russian roulette all in
    # thanks gautam
    if random.randint(1, 20) > 19:
        # all in
        return (chips, memory)
    
    pot = 0 
    for _p in state.pots:
        pot += _p.value
        
    board_eval = evaluate_board(state.player_cards, state.community_cards)

    # check the river, whatever i have.
    # if bet into, then go from there.
    if my_bet == 0 and max(state.bet_money) == 0:
        return (0, memory)
    


    # from here, either all in if i have something or just fold. 
    # or call if we're unconfident in 2 pair / top pair       

    if board_eval > 9 or board_eval == 7:
        # jam.
        return (chips, memory)
    
    if is_straight_draw(state.community_cards) or is_flush_draw(state.community_cards):
        return (-1, memory)

    if board_eval == 6:
        r = random.randint(1, 3)
        if r == 1:
            return (-1, memory)
        
        return (chips, memory) # jam a set on an emptyish (hopefully board)

    
    # 2 pair code merged in below.


    # high pair i would lvoe to code in a call
    # but ts seems to complicated

    # ok we try
    # check for no 3 in a rows/3 of the same suit to maybe call
    if board_eval == 4 or board_eval == 5:
        r = random.randint(1, 4)
        if r == 1 or (r == 2 and board_eval == 4):
            return (-1, memory)
        
        # check 3 in a row / 3 of the same suit
        # if either condition is met also fold.

        # 3 of the same suit
        # iterate over and add in a suit to see if you can get 4 of
        if is_flush_draw(state.community_cards + ['2s']) or is_flush_draw(state.community_cards + ['2c']) or is_flush_draw(state.community_cards + ['2d']) or is_flush_draw(state.community_cards + ['2h']):
            return (-1, memory)

        # 3 of the same
        _arr = []
        _ls = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
        for c in state.community_cards:
            _arr.append(_ls.index(c[0]) + 2)
            if c[0] == 'a':
                _arr.append(1)
        
        # 1, 2, 3, ..., 12, 13, 14
        f = False
        for i in range(1, 13):
            if i in _arr and i + 1 in _arr and i + 2 in _arr:
                f = True
                break
        
        if f:
            return (-1, memory)
        
        return (min(chips, max(state.bet_money)), memory)
    
    # fold garbage
    return (-1, memory)


    ###################################### </river>

    # we're done :)






""" turn a hand into 'standard' preflop hand notation """
def convert_hand(hand):
    # hand is a list of str ints
    # 2s/2h/2d/2c -> ac/ah/ad/as

    _rank = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']

    f, s = hand[0].lower(), hand[1].lower()

    if _rank.index(s[0]) == _rank.index(f[0]):
        return f[0]*2 # e.g. 22
    
    
    if _rank.index(s[0]) > _rank.index(f[0]):
        f, s = s, f # swap hands

    if f[1] == s[1]:
        return f[0] + s[0] + 's' # suited
    
    return f[0] + s[0] + 'o'






""" 
return number based on what "cards" there are

straight flush = 13
quads = 12
full house / boat = 11

high flush = 9
low flush = 8
straight = 7
set = 6
two pair = 5
high pair/over pair = 4 
med/low pair = 3
ace high / king high = 2
abosultely fucking nothing = 1

edge cases // fold (set on the board, etc.) = 0


high flush draw = 40
low flush draw = 30

2 card straight draw = 20
1 card straight draw = 10
"""


def evaluate_board(cards, board):
    # after flop
    
    if is_quads(board):
        return 0

    if is_quads(cards + board):
        return 12
    
    if is_boat(board):
        return 0

    if is_boat(cards + board):
        return 11
    
    _flush = is_flush(cards + board)
    _straight = is_straight(cards + board)

    if _straight and _flush:
        return 13
    
    
    if len(board) == 3:       
        if _straight:
            return 7

        if _flush:
            if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                return 9
            
            return 8
    

        if is_flush_draw(cards + board):
            # high flush draw = 40, low flush draw = 30

            if board[0][1] == board[1][1] == board[2][1]:
                # ehrm its the card in my hand.
                if cards[0][1] == board[0][1] and cards[0][0] in ['a', 'k', 'q', 'j', 't']:
                    return 40

                if cards[1][1] == board[0][1] and cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                    return 40
                
                return 30
            
            if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                return 40

            return 30
            
            # max card in my hand

        if is_straight_draw(cards + board) == 2:
            return 20
        
        if is_straight_draw(cards + board):
            return 10
        
        if is_set(board):
            return 0
        
        if is_set(cards + board):
            return 6

        if is_two_pair(cards + board):
            return 5

        if is_pair(cards + board) and not is_pair(board):
            return 3 + is_high_pair(cards, board)
        
        if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
            return 2
        
        return 1
    
    if len(board) == 4:
        if _straight:
            return 7

        if _flush:
            if board[0][1] != board[1][1] or board[0][1] != board[2][1] or board[0][1] != board[3][1]:
                if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                    return 9
                
                return 8
        
            # 4 cards on the board make a flush already.
            if cards[0][1] == board[0][1] and cards[0][0] in ['a', 'k', 'q', 'j', 't']:
                return 9

            if cards[1][1] == board[0][1] and cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                return 9
                
            return 8
    

        if is_flush_draw(cards + board):
            # high flush draw = 40, low flush draw = 30

            if is_flush_draw(board):
                # you probably have nothing. get out
                return 0

            if board[0][1] == board[1][1] == board[2][1]:
                # ehrm its the card in my hand.
                if cards[0][1] == board[0][1] and cards[0][0] in ['a', 'k', 'q', 'j', 't']:
                    return 40

                if cards[1][1] == board[0][1] and cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                    return 40
                
                return 30
            
            if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                return 40

            return 30
            
            # max card in my hand

        if is_straight_draw(board):
            return 0
        
        if is_straight_draw(cards + board) == 2:
            return 20
        
        if is_straight_draw(cards + board):
            return 10
        
        if is_set(board):
            return 0
        
        if is_set(cards + board):
            return 6

        if is_two_pair(board):
            return 0
        
        if is_two_pair(cards + board):
            return 5

        if is_pair(cards + board) and not is_pair(board):
            return 3 + is_high_pair(cards, board)
        
        if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
            return 2
        
        return 1

    # len(board) == 5
    if is_straight(board) or is_flush(board):
        return 0
    
    if _straight:
        return 7

    if _flush:
        # check if 3 card flush
        _suits = [board[i][1] for i in range(5)]
        if _suits.count('s') == 3 or _suits.count('h') == 3 or _suits.count('c') == 3 or _suits.count('d') == 3:
            if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
                return 9
            
            return 8
    
        # 4 cards on the board make a flush already.
        if cards[0][1] == board[0][1] and cards[0][0] in ['a', 'k', 'q', 'j', 't']:
            return 9

        if cards[1][1] == board[0][1] and cards[1][0] in ['a', 'k', 'q', 'j', 't']:
            return 9
            
        return 8

    
    if is_set(board):
        return 0
    
    if is_set(cards + board):
        return 6

    if is_two_pair(board):
        return 0
    
    if is_two_pair(cards + board):
        return 5

    if is_pair(cards + board) and not is_pair(board):
        return 3 + is_high_pair(cards, board)
    
    if cards[0][0] in ['a', 'k', 'q', 'j', 't'] or cards[1][0] in ['a', 'k', 'q', 'j', 't']:
        return 2
    
    return 1


##### all functions below here have been tested.


def is_x(cards, x):
    d = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 't': 10, 'j': 11, 'q': 12, 'k': 13, 'a': 14}

    a = []
    for c in cards:
        a.append(d[c[0]])
    
    for i in range(2, 15):
        if a.count(i) > x - 1:
            return True
    
    return False

def is_quads(cards):
    return is_x(cards, 4)

def is_boat(cards):
    d = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 't': 10, 'j': 11, 'q': 12, 'k': 13, 'a': 14}

    a = []
    for c in cards:
        a.append(d[c[0]])
    
    v = -1
    for i in range(2, 15):
        if a.count(i) > 2:
            v = i
            break
    
    if v < 0:
        return False
    
    # set of 3 on the board

    for i in range(2, 15):
        if i == v:
            continue 

        if a.count(i) > 1:
            return True
    
    return False

def is_flush(cards):
    suits = []
    for c in cards:
        suits.append(c[1])

    if suits.count('s') > 4 or suits.count('h') > 4 or suits.count('d') > 4 or suits.count('c') > 4:
        return True 

    return False

def is_flush_draw(cards):
    suits = []
    for c in cards:
        suits.append(c[1])

    if suits.count('s') == 4 or suits.count('h') == 4 or suits.count('d') == 4 or suits.count('c') == 4:
        return True 

    return False

def is_straight(cards):
    _aux = []
    for c in cards:
        d = c[0]

        if ord('1') < ord(d) and ord(':') > ord(d):
            # number
            _aux.append(int(d))
            continue 

        if d == 'a':
            _aux.append(14)
            continue 

        mapping = {'k': 13, 'q': 12, 'j': 11, 't': 10}
        _aux.append(mapping[d])
        continue 
    
    _aux.sort()

    # check ace low straight 
    if 14 in _aux and 2 in _aux and 3 in _aux and 4 in _aux and 5 in _aux:
        return True
    
    for i in range(2, 11):
        if i in _aux and i + 1 in _aux and i + 2 in _aux and i + 3 in _aux and i + 4 in _aux:
            return True 
    
    return False

# return 0 (False), 1 (1 card open), 2 (2 cards open)
# 0 -> False
# 1 -> 1 card open
# 2 -> 2 cards open
# this function is actually wrong slightly
# if board is [8, t, j, q, a], both k and 9 satisfy but this returns 1 card open.
def is_straight_draw(cards):
    _aux = []
    for c in cards:
        d = c[0]

        if ord('1') < ord(d) and ord(':') > ord(d):
            # number
            _aux.append(int(d))
            continue 

        if d == 'a':
            _aux.append(14)
            continue 

        mapping = {'k': 13, 'q': 12, 'j': 11, 't': 10}
        _aux.append(mapping[d])
        continue 
    
    _aux.sort()

    # check ace low straight 
    if 14 in _aux and 2 in _aux and 3 in _aux and 4 in _aux:
        return 1
    
    if 14 in _aux and 13 in _aux and 12 in _aux and 11 in _aux:
        return 1
    
    for i in range(2, 11):
        if i in _aux and i + 1 in _aux and i + 2 in _aux and i + 3 in _aux:
            return 2 

    # check for open enders via appending values
    # append 2/3/.../k
    for i in [2, 3, 4, 5, 6, 7, 8, 9, 't', 'j', 'q', 'k']:
        if is_straight(cards + [str(i) + 's']):
            return 1
    
    
    return 0

def is_set(cards):
    return is_x(cards, 3)

def is_pair(cards):
    return is_x(cards, 2)

# guaranteed that cards + board has a pair on it
# 0/1 for low/high pair
def is_high_pair(cards, board):
    l = ['a', 'k', 'q', 'j', 't', '9', '8', '7', '6', '5', '4', '3', '2']

    max_pair = 0
    for b in board:
        max_pair = max(max_pair, 14 - l.index(b[0]))

    if 14 - l.index(cards[0][0]) == max_pair or 14 - l.index(cards[1][0]) == max_pair:
        return 1

    # check if theres an over pair.
    
    for ind in range(14 - max_pair):
        if l[ind] == cards[0][0] == cards[1][0]:
            return 1
    
    return 0


def is_two_pair(cards):
    d = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 't': 10, 'j': 11, 'q': 12, 'k': 13, 'a': 14}

    a = []
    for c in cards:
        a.append(d[c[0]])
    
    v = 0
    for i in range(2, 15):
        if a.count(i) > 1:
            v += 1

    
    return v > 1

#####




