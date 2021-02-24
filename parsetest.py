import re

import emoji
import itertools

number_aliases = {
    ':keycap_0:': ['0'],
    ':O_button_(blood_type):': ['0'],
    ':heavy_large_circle:': ['0'],
    ':keycap_1:': ['1'],
    ':1st_place_medal:': ['1'],
    ':keycap_2:': ['2'],
    ':2nd_place_medal:': ['2'],
    ':keycap_3:': ['3'],
    ':3rd_place_medal:': ['3'],
    ':evergreen_tree:': ['3'],
    ':deciduous_tree:': ['3'],
    ':palm_tree:': ['3'],
    ':christmas_tree:': ['3'],
    ':cactus:': ['3'],
    ':shamrock:': ['3'],
    ':keycap_4:': ['4'],
    ':four_leaf_clover:': ['4'],
    ':keycap_5:': ['5'],
    ':keycap_6:': ['6'],
    ':keycap_7:': ['7'],
    ':keycap_8:': ['8'],
    ':pool_8_ball:': ['8'],
    ':keycap_9:': ['9'],
    ':keycap_10:': ['10'],
    ':ringed_planet:': ['42'],
    ':OK_hand:': ['69'],
    ':cancer:': ['69'],
    ':hundred_points:': ['100', '00'],
    ':input_numbers:': ['1234']
}

PARSE_DICT = {v: number_aliases[k] for k, v in emoji.unicode_codes.EMOJI_UNICODE_ENGLISH.items() if k in number_aliases.keys()}


def parsed(number: str):
    number = emoji.demojize()
    plist = [c for c in number]
    emojis = []
    for pos, c in enumerate(number):
        if c in emoji.unicode_codes.UNICODE_EMOJI['en']:
            emojis.append((pos, c))
        elif c in '1234567890' and pos < len(number) - 1 and number[pos + 1] == '':
            pass

    for e, i in emojis:
        plist[i] = number_aliases[emoji.demojize(e)]

    return [''.join(i) for i in itertools.product(*plist)]


def parsealiases(string):
    def replace(match):
        codes_dict = number_aliases
        val = codes_dict.get(match.group(0), match.group(0))
        print(val)
        return ':' + val[1:-1] + ':'

    return re.sub(u'\ufe0f', '', (emoji.get_emoji_regexp().sub(replace, string)))


print(PARSE_DICT)

print(parsealiases(emoji.emojize('test:keycap_9:123')))
#print(emoji.demojize(':keycap_9:'))
