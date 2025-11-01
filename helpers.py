from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # import types for annotations only to avoid a runtime circular import
    from bot import GameState, Pot


# returns list of players, index corresponds to player index in GameState
def get_player_list(state: GameState) -> list[str]:
    return state.players

# returns the amount needed to call the current bet
def amount_to_call(state: GameState) -> int:
    current_bet = max(state.bet_money)
    player_bet = state.bet_money[state.index_to_action]
    return current_bet - player_bet

def get_my_pots(state: GameState) -> list[Pot]:
    my_index = state.index_to_action
    my_pots = []
    for pot in state.pots:
        if state.players[my_index] in pot.players:
            my_pots.append(pot)
    return my_pots

def pot_odds(state: GameState) -> float:
    my_pots = get_my_pots(state)
    total_pot = sum(pot.value for pot in my_pots)
    to_call = amount_to_call(state)
    if to_call == 0:
        return float('inf')  # Infinite odds if no call is needed
    return total_pot / to_call

def required_equity_for_call(state: GameState) -> float:
    to_call = amount_to_call(state)
    my_pots = get_my_pots(state)
    total_pot = sum(pot.value for pot in my_pots)
    if total_pot + to_call == 0:
        return 0.0
    return to_call / (total_pot + to_call)

def get_best_hand(cards: list[str]) -> tuple[int, list[str]]:
    # Evaluate the best 5-card poker hand from the given cards (up to 7 cards).
    # Returns a tuple (hand_strength:int, best_five_cards:list[str]) where
    # higher hand_strength is a stronger hand. Strength mapping:
    # 8: Straight Flush, 7: Four of a Kind, 6: Full House, 5: Flush,
    # 4: Straight, 3: Three of a Kind, 2: Two Pair, 1: One Pair, 0: High Card
    from itertools import combinations

    RANK_ORDER = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                  't': 10, 'j': 11, 'q': 12, 'k': 13, 'a': 14}

    HAND_NAMES = {
        8: 'Straight Flush',
        7: 'Four of a Kind',
        6: 'Full House',
        5: 'Flush',
        4: 'Straight',
        3: 'Three of a Kind',
        2: 'Two Pair',
        1: 'One Pair',
        0: 'High Card'
    }

    def parse_card(card: str) -> tuple[int, str]:
        if len(card) != 2:
            raise ValueError(f"Invalid card string: {card}")
        r = card[0].lower()
        s = card[1].lower()
        if r not in RANK_ORDER:
            raise ValueError(f"Invalid rank: {r}")
        return (RANK_ORDER[r], s)

    def is_straight(ranks: list[int]) -> int:
        # ranks is a sorted list of unique ranks descending
        if not ranks:
            return 0
        # consider Ace low straight
        ranks_set = set(ranks)
        # try highest to lowest
        for high in range(max(ranks), 4, -1):
            needed = {high - i for i in range(5)}
            if needed.issubset(ranks_set):
                return high
        # wheel straight A-2-3-4-5
        if {14, 2, 3, 4, 5}.issubset(ranks_set):
            return 5
        return 0

    def evaluate_five(cards5: list[str]) -> tuple[int, list[int]]:
        # returns (category, tiebreakers_list) where higher tuple > better hand
        parsed = [parse_card(c) for c in cards5]
        ranks = sorted((r for r, _ in parsed), reverse=True)
        suits = [s for _, s in parsed]

        # rank counts
        from collections import Counter
        cnt = Counter(ranks)
        counts = sorted(((count, rank) for rank, count in cnt.items()), reverse=True)

        is_flush = len(set(suits)) == 1
        unique_ranks_desc = sorted(set(ranks), reverse=True)
        straight_high = is_straight(unique_ranks_desc)

        # Straight flush
        if is_flush and straight_high:
            return (8, [straight_high])

        # Four of a kind
        if counts[0][0] == 4:
            four_rank = counts[0][1]
            kicker = max(r for r in ranks if r != four_rank)
            return (7, [four_rank, kicker])

        # Full house
        if counts[0][0] == 3 and len(counts) > 1 and counts[1][0] >= 2:
            three_rank = counts[0][1]
            pair_rank = counts[1][1]
            return (6, [three_rank, pair_rank])

        # Flush
        if is_flush:
            return (5, ranks)

        # Straight
        if straight_high:
            return (4, [straight_high])

        # Three of a kind
        if counts[0][0] == 3:
            three_rank = counts[0][1]
            kickers = sorted((r for r in ranks if r != three_rank), reverse=True)
            return (3, [three_rank] + kickers)

        # Two pair
        if counts[0][0] == 2 and len(counts) > 1 and counts[1][0] == 2:
            high_pair = max(counts[0][1], counts[1][1])
            low_pair = min(counts[0][1], counts[1][1])
            kicker = max(r for r in ranks if r != high_pair and r != low_pair)
            return (2, [high_pair, low_pair, kicker])

        # One pair
        if counts[0][0] == 2:
            pair_rank = counts[0][1]
            kickers = sorted((r for r in ranks if r != pair_rank), reverse=True)
            return (1, [pair_rank] + kickers)

        # High card
        return (0, ranks)

    # consider all 5-card combinations (cards may be 5..7 long)
    best = (-1, [])
    best_five = None
    for combo in combinations(cards, 5):
        val = evaluate_five(list(combo))
        if val > best:
            best = val
            best_five = combo

    if best[0] < 0:
        return (-1, [])

    # Return numeric strength and the 5 cards that produce it
    return (best[0], list(best_five))


def get_best_hand_from(hand: list[str], community: list[str]) -> tuple[int, list[str]]:
    """
    Evaluate the best 5-card poker hand given a player's hole `hand` and the `community` cards.

    Args:
        hand: list of 2 card strings (e.g. ['ah', 'kc'])
        community: list of 3..5 community card strings

    Returns:
        tuple: same format as `get_best_hand`, e.g. (6, ['ah','as','ad','kh','kc'])
    """
    if not isinstance(hand, list) or not isinstance(community, list):
        raise TypeError("hand and community must be lists of card strings")
    if len(hand) != 2:
        # allow len 0..2 for flexibility, but warn/raise for >2
        if len(hand) > 2:
            raise ValueError("hand should contain at most 2 cards")
    # combine and delegate to get_best_hand
    combined = list(hand) + list(community)
    return get_best_hand(combined)


def fold() -> int:
    return -1

def check() -> int:
    return 0

def call(state: GameState) -> int:
    return amount_to_call(state)

def all_in(state: GameState) -> int:
    my_index = state.index_to_action
    return state.held_money[my_index]

def min_raise(state: GameState) -> int:
    """
    Compute the minimum amount (chips) the current player must put in this action to make a legal
    raise according to standard poker rules.

    The rule implemented:
        - Determine the size of the last raise in the current betting round as
            current_bet - previous_highest_bet
        - If there is no previous raise (no lower bet), use the big blind as the minimum raise size
        - The target total bet to reach is: current_bet + min_raise_size
        - Return the amount the current player must put in (target_total - my_bet)
    """
    current_bet = max(state.bet_money) if state.bet_money else 0
    my_index = state.index_to_action
    my_bet = state.bet_money[my_index]

    # find the highest bet that is strictly less than the current max bet
    # exclude folded players (bet_money == -1)
    lower_bets = [b for b in state.bet_money if 0 <= b < current_bet]
    
    if lower_bets:
        prev_max = max(lower_bets)
        previous_raise = current_bet - prev_max
    else:
        # if no lower bet exists, fall back to big blind
        previous_raise = state.big_blind

    min_raise_size = max(previous_raise, state.big_blind)
    target_total_bet = current_bet + min_raise_size
    
    # amount the player must put in this action to reach target_total_bet
    return max(0, target_total_bet - my_bet)

# Check if a proposed bet amount is valid in the current game state
def is_valid_bet(state: GameState, amount: int) -> bool:
    my_index = state.index_to_action
    if amount == -1:
        return True  # fold is always valid
    to_call = amount_to_call(state)
    current_bet = max(state.bet_money)
    my_bet = state.bet_money[my_index]
    my_held = state.held_money[my_index]
    
    if amount == 0:
        # check
        return to_call == 0
    elif amount < 0:
        return False  # negative bets (other than -1 for fold) are invalid
    else:
        # call or raise
        total_bet = my_bet + amount
        if total_bet < current_bet:
            return False  # cannot bet less than current bet (invalid call)
        if total_bet > my_bet + my_held:
            return False  # cannot bet more than held money (invalid all-in)
        if total_bet > current_bet:
            # it's a raise, must meet min raise requirement
            min_raise_amount = min_raise(state)
            if amount < min_raise_amount:
                return False
        return True