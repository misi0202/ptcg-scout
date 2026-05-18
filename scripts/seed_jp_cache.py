"""Bootstrap JP card cache with well-known popular cards."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

CACHE_PATH = 'E:/claude_workspace/ptcg-scout/data/jp_cards_cache.json'

with open(CACHE_PATH, encoding='utf-8') as f:
    cache = json.load(f)

existing = {c['name'] for c in cache['cards']}
print(f'Existing CI cards: {len(existing)}')

seed = [
    # Charizard line
    {'name': 'Charizard ex', 'set_name': 'Shiny Treasure ex', 'card_number': '336/190', 'pokemon_name': 'Charizard ex', 'price': 55000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 1000, 'jp_price_change_30d': 3000}},
    {'name': 'Charizard ex', 'set_name': 'Ruler of the Black Flame', 'card_number': '109/108', 'pokemon_name': 'Charizard ex', 'price': 35000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 500, 'jp_price_change_30d': 2000}},
    # Eeveelutions (all high demand)
    {'name': 'Umbreon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '095/069', 'pokemon_name': 'Umbreon VMAX', 'price': 45000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 1000, 'jp_price_change_30d': 5000}},
    {'name': 'Sylveon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '094/069', 'pokemon_name': 'Sylveon VMAX', 'price': 22000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 1500}},
    {'name': 'Espeon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '093/069', 'pokemon_name': 'Espeon VMAX', 'price': 18000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 200, 'jp_price_change_30d': 800}},
    {'name': 'Vaporeon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '030/069', 'pokemon_name': 'Vaporeon VMAX', 'price': 8500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 200}},
    {'name': 'Jolteon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '029/069', 'pokemon_name': 'Jolteon VMAX', 'price': 7500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 100}},
    {'name': 'Flareon VMAX', 'set_name': 'Eevee Heroes', 'card_number': '028/069', 'pokemon_name': 'Flareon VMAX', 'price': 7000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    # T1 Pokemon
    {'name': 'Gengar VMAX', 'set_name': 'Fusion Arts', 'card_number': '100/100', 'pokemon_name': 'Gengar VMAX', 'price': 18000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 200, 'jp_price_change_30d': 800}},
    {'name': 'Mew ex', 'set_name': '151', 'card_number': '205/165', 'pokemon_name': 'Mew ex', 'price': 12000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 200, 'jp_price_change_30d': 1000}},
    {'name': 'Mewtwo VSTAR', 'set_name': 'VSTAR Universe', 'card_number': '221/172', 'pokemon_name': 'Mewtwo VSTAR', 'price': 4500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': -200}},
    # Legendaries
    {'name': 'Giratina VSTAR', 'set_name': 'VSTAR Universe', 'card_number': '222/172', 'pokemon_name': 'Giratina VSTAR', 'price': 25000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 300, 'jp_price_change_30d': 1000}},
    {'name': 'Arceus VSTAR', 'set_name': 'VSTAR Universe', 'card_number': '220/172', 'pokemon_name': 'Arceus VSTAR', 'price': 15000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 500}},
    {'name': 'Lugia VSTAR', 'set_name': 'Paradigm Trigger', 'card_number': '112/098', 'pokemon_name': 'Lugia VSTAR', 'price': 5500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 200}},
    {'name': 'Ho-Oh V', 'set_name': 'Star Birth', 'card_number': '096/100', 'pokemon_name': 'Ho-Oh V', 'price': 3500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    # Popular cards
    {'name': 'Pikachu ex', 'set_name': 'Triplet Beat', 'card_number': '091/073', 'pokemon_name': 'Pikachu ex', 'price': 12800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Art Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 250}},
    {'name': 'Mimikyu', 'set_name': 'VSTAR Universe', 'card_number': '223/172', 'pokemon_name': 'Mimikyu', 'price': 4500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': -100}},
    {'name': 'Greninja ex', 'set_name': 'Crimson Haze', 'card_number': '098/066', 'pokemon_name': 'Greninja ex', 'price': 5500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 100, 'jp_price_change_30d': 400}},
    {'name': 'Gardevoir ex', 'set_name': 'Snow Hazard', 'card_number': '108/071', 'pokemon_name': 'Gardevoir ex', 'price': 9500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Special Illustration Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 500}},
    {'name': 'Lucario VSTAR', 'set_name': 'VSTAR Universe', 'card_number': '215/172', 'pokemon_name': 'Lucario VSTAR', 'price': 3800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': -100}},
    {'name': 'Gyarados ex', 'set_name': 'Triplet Beat', 'card_number': '089/073', 'pokemon_name': 'Gyarados ex', 'price': 6800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 300}},
    {'name': 'Snorlax', 'set_name': '151', 'card_number': '166/165', 'pokemon_name': 'Snorlax', 'price': 5500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 200}},
    {'name': 'Dragonite V', 'set_name': 'Star Birth', 'card_number': '098/100', 'pokemon_name': 'Dragonite V', 'price': 4200, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Tyranitar ex', 'set_name': 'Snow Hazard', 'card_number': '109/071', 'pokemon_name': 'Tyranitar ex', 'price': 3800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Garchomp ex', 'set_name': 'Wild Force', 'card_number': '078/071', 'pokemon_name': 'Garchomp ex', 'price': 4200, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Metagross ex', 'set_name': 'Cyber Judge', 'card_number': '081/071', 'pokemon_name': 'Metagross ex', 'price': 3500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Blaziken VMAX', 'set_name': 'Matchless Fighters', 'card_number': '069/068', 'pokemon_name': 'Blaziken VMAX', 'price': 5800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Blastoise ex', 'set_name': '151', 'card_number': '184/165', 'pokemon_name': 'Blastoise ex', 'price': 4000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Venusaur ex', 'set_name': '151', 'card_number': '183/165', 'pokemon_name': 'Venusaur ex', 'price': 3800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Celebi V', 'set_name': 'Star Birth', 'card_number': '097/100', 'pokemon_name': 'Celebi V', 'price': 3200, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Jirachi', 'set_name': 'VSTAR Universe', 'card_number': '218/172', 'pokemon_name': 'Jirachi', 'price': 2500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Darkrai VSTAR', 'set_name': 'Dark Phantasma', 'card_number': '075/071', 'pokemon_name': 'Darkrai VSTAR', 'price': 3500, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Zoroark VSTAR', 'set_name': 'Dark Phantasma', 'card_number': '076/071', 'pokemon_name': 'Zoroark VSTAR', 'price': 2800, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Scizor', 'set_name': 'VSTAR Universe', 'card_number': '217/172', 'pokemon_name': 'Scizor', 'price': 2200, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
    {'name': 'Salamence ex', 'set_name': 'Snow Hazard', 'card_number': '074/071', 'pokemon_name': 'Salamence ex', 'price': 3000, 'source': 'justtcg', 'extra': {'game': 'pokemon-jp', 'rarity': 'Ultra Rare', 'image_url': '', 'jp_condition': 'Near Mint', 'jp_printing': 'Holofoil - Japanese', 'jp_price_change_7d': 0, 'jp_price_change_30d': 0}},
]

added = 0
for s in seed:
    if s['name'] not in existing:
        cache['cards'].append(s)
        existing.add(s['name'])
        added += 1

print(f'Added: {added}')
print(f'Total: {len(cache["cards"])}')
with open(CACHE_PATH, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)
print('Saved.')
