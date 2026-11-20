import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import base64
import time
from image_generator import image_generator

CHALLENGES = [
    {
        'id': 'coffee-latte-book',
        'title': 'A Quiet Chapter',
        'gen_prompt': 'A warm white ceramic coffee mug with heart-shaped latte art foam sitting next to a closed blue hardcover book on a clean dark wooden table, soft morning daylight, clean minimalist composition, sharp focus',
        'brief': 'A warm ceramic mug with heart latte art in the foam sitting next to a closed hardcover book on a clean wooden table.',
        'visual_goals': 'White ceramic coffee mug, heart pattern in latte foam, closed blue hardcover book, clean dark wooden table.',
        'inspiration_keywords': ['Coffee Mug', 'Heart Latte Art', 'Closed Book', 'Wooden Table', 'Morning Light'],
        'key_subjects': ['ceramic coffee mug', 'heart latte art', 'hardcover book', 'wooden table'],
        'action': 'resting on the table next to the book',
        'lighting_mood': 'warm soft morning daylight',
        'evaluation_focus': 'Presence of the coffee mug with heart latte art, the book beside it, and the wooden table.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'cat-sunglasses-chair',
        'title': 'The Sunlit Solarium',
        'gen_prompt': 'A fluffy white cat wearing stylish black sunglasses sitting comfortably on a bright yellow armchair in a clean sunlit room with plain background, minimalist, sharp focus',
        'brief': 'A fluffy white cat wearing black sunglasses sitting on a bright yellow armchair in a sunlit room.',
        'visual_goals': 'Fluffy white cat, black sunglasses on face, bright yellow armchair, sunny clean room.',
        'inspiration_keywords': ['White Cat', 'Black Sunglasses', 'Yellow Armchair', 'Sunlit Room'],
        'key_subjects': ['fluffy white cat', 'black sunglasses', 'bright yellow armchair'],
        'action': 'sitting upright on the armchair',
        'lighting_mood': 'bright warm daylight',
        'evaluation_focus': 'Recreation of the white cat wearing sunglasses on a bright yellow chair.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'dog-party-cake',
        'title': 'Another Year Wiser',
        'gen_prompt': 'A cute golden retriever puppy wearing a colorful pointed cone party hat sitting in front of a small birthday cupcake with a single lit candle on a clean white table, cheerful lighting, clean background',
        'brief': 'A happy golden retriever wearing a colorful party hat in front of a small birthday cake with a single lit candle.',
        'visual_goals': 'Smiling golden retriever, pointed cone party hat, small cake with one glowing candle, clean background.',
        'inspiration_keywords': ['Golden Retriever', 'Party Hat', 'Small Cake', 'Lit Candle'],
        'key_subjects': ['golden retriever dog', 'pointed party hat', 'cake with lit candle'],
        'action': 'smiling behind the birthday cake',
        'lighting_mood': 'cheerful warm indoor lighting',
        'evaluation_focus': 'Golden retriever wearing a party hat with a lit candle on the cake.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'frog-mushroom-umbrella',
        'title': 'Under the Crimson Canopy',
        'gen_prompt': 'A small bright green tree frog sitting calmly on top of a red toadstool mushroom with white polka dots on soft green moss, clean macro photography, soft natural daylight, simple background',
        'brief': 'A small bright green frog sitting on a red mushroom with white polka dots on green moss.',
        'visual_goals': 'Bright green frog, red toadstool mushroom with white polka dots, soft green moss, simple background.',
        'inspiration_keywords': ['Green Tree Frog', 'Red Toadstool Mushroom', 'White Polka Dots', 'Green Moss'],
        'key_subjects': ['green tree frog', 'red mushroom with white spots', 'green moss'],
        'action': 'perched calmly on the mushroom cap',
        'lighting_mood': 'soft diffused natural light',
        'evaluation_focus': 'Green frog sitting on the red-and-white spotted mushroom.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'yellow-rubber-duck',
        'title': 'The Sunny Drift',
        'gen_prompt': 'A classic bright yellow rubber duck floating in clean clear blue water with white soap bubbles, studio lighting, clean minimalist composition, sharp focus',
        'brief': 'A classic bright yellow rubber duck floating in clean blue water with white soap bubbles.',
        'visual_goals': 'Bright yellow rubber duck, clear blue water, fluffy white soap bubbles, clean composition.',
        'inspiration_keywords': ['Yellow Rubber Duck', 'Blue Water', 'Soap Bubbles', 'Clean Minimalist'],
        'key_subjects': ['yellow rubber duck', 'clear blue water', 'white soap bubbles'],
        'action': 'floating on calm water with bubbles',
        'lighting_mood': 'clean bright studio lighting',
        'evaluation_focus': 'Yellow rubber duck floating in blue water with soap bubbles.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'chocolate-cake-slice',
        'title': 'Midnight Confection',
        'gen_prompt': 'A delicious slice of rich dark chocolate cake topped with a fresh glossy red strawberry on a clean white round ceramic plate on a wooden table, cafe lighting, clean view',
        'brief': 'A slice of chocolate cake topped with a fresh red strawberry on a white plate.',
        'visual_goals': 'Layered dark chocolate cake, fresh red strawberry on top, clean white plate, wooden table.',
        'inspiration_keywords': ['Chocolate Cake', 'Red Strawberry', 'White Plate', 'Wooden Table'],
        'key_subjects': ['slice of chocolate cake', 'fresh red strawberry', 'white ceramic plate'],
        'action': 'served on the plate',
        'lighting_mood': 'warm soft cafe lighting',
        'evaluation_focus': 'Chocolate cake slice with a red strawberry on a white plate.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'red-apple-table',
        'title': 'The Crimson Harvest',
        'gen_prompt': 'A single fresh shiny bright red apple with a small green leaf and water droplets sitting on a clean polished light wooden table, soft natural daylight, minimalist studio',
        'brief': 'A fresh shiny red apple with a small green leaf on a clean wooden table.',
        'visual_goals': 'Glossy red apple, small green leaf, water droplets, light wooden table.',
        'inspiration_keywords': ['Red Apple', 'Green Leaf', 'Wooden Table', 'Clean Minimalist'],
        'key_subjects': ['shiny red apple', 'small green leaf', 'wooden table'],
        'action': 'resting on the clean table surface',
        'lighting_mood': 'soft bright natural daylight',
        'evaluation_focus': 'Shiny red apple with green leaf on a wooden table.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'red-rose-vase',
        'title': 'Velvet Petal',
        'gen_prompt': 'A single blooming deep red rose with green leaves in a clear cylindrical glass vase filled with water on a clean white marble tabletop, elegant soft light, clean background',
        'brief': 'A single blooming red rose in a clear glass vase of water on a clean white surface.',
        'visual_goals': 'Deep red rose bloom, green stem and leaves, clear glass vase with water, white marble surface.',
        'inspiration_keywords': ['Red Rose', 'Glass Vase', 'Clear Water', 'White Marble Table'],
        'key_subjects': ['single red rose', 'clear glass vase', 'white table'],
        'action': 'standing in the vase',
        'lighting_mood': 'soft elegant natural light',
        'evaluation_focus': 'Single red rose in a clear glass vase on a clean surface.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'orange-juice-glass',
        'title': 'Morning Citrus',
        'gen_prompt': 'A tall clear drinking glass filled with fresh vibrant orange juice and ice cubes, garnished with an orange slice on the rim and a striped straw on a clean wooden table, sunny morning light',
        'brief': 'A tall glass of fresh orange juice with ice cubes, an orange slice on the rim, and a straw on a table.',
        'visual_goals': 'Tall glass of orange juice, visible ice cubes, fresh orange wheel slice on rim, striped straw, wooden table.',
        'inspiration_keywords': ['Orange Juice', 'Tall Glass', 'Orange Slice', 'Ice Cubes', 'Straw'],
        'key_subjects': ['glass of orange juice', 'ice cubes', 'orange slice', 'straw'],
        'action': 'standing on the table with ice and straw',
        'lighting_mood': 'bright sunny morning light',
        'evaluation_focus': 'Glass of orange juice with ice, orange slice on the rim, and straw.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'pancakes-syrup-butter',
        'title': 'Golden Morning',
        'gen_prompt': 'A neat stack of three golden fluffy pancakes topped with a melting square of yellow butter and dripping warm maple syrup on a clean ceramic plate, breakfast lighting',
        'brief': 'A stack of fluffy pancakes topped with melting butter and dripping maple syrup on a plate.',
        'visual_goals': 'Stack of three pancakes, melting square of butter on top, dripping maple syrup, clean round plate.',
        'inspiration_keywords': ['Pancakes', 'Melting Butter', 'Maple Syrup', 'Breakfast Plate'],
        'key_subjects': ['stack of pancakes', 'melting yellow butter', 'maple syrup', 'plate'],
        'action': 'stacked neatly with syrup dripping',
        'lighting_mood': 'warm cheerful breakfast light',
        'evaluation_focus': 'Stack of pancakes with melting butter square and syrup.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'red-telephone-desk',
        'title': 'The Direct Line',
        'gen_prompt': 'A classic bright red vintage rotary dial telephone with coiled cord sitting on a clean dark polished wooden desk, warm soft indoor lighting, minimalist composition',
        'brief': 'A classic bright red vintage rotary dial telephone sitting on a clean wooden desk.',
        'visual_goals': 'Glossy red rotary dial telephone, coiled black cord, dark polished wooden desk, simple background.',
        'inspiration_keywords': ['Vintage Red Telephone', 'Rotary Dial', 'Coiled Cord', 'Wooden Desk'],
        'key_subjects': ['red rotary telephone', 'coiled cord', 'wooden desk'],
        'action': 'resting on the executive wooden desk',
        'lighting_mood': 'warm focused indoor glow',
        'evaluation_focus': 'Bright red rotary telephone on a clean wooden desk.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'vintage-red-bicycle',
        'title': 'Passage of Summer',
        'gen_prompt': 'A classic bright red vintage bicycle with a brown leather seat and a woven wicker front basket filled with yellow sunflowers, parked against a clean plain white wall, sunny daylight',
        'brief': 'A bright red vintage bicycle with a front wicker basket of yellow flowers against a clean plain white wall.',
        'visual_goals': 'Bright red bicycle frame, wicker front basket with yellow sunflowers, plain white wall background.',
        'inspiration_keywords': ['Red Bicycle', 'Wicker Basket', 'Yellow Sunflowers', 'White Wall'],
        'key_subjects': ['red vintage bicycle', 'wicker basket with yellow sunflowers', 'white wall'],
        'action': 'parked against the plain wall',
        'lighting_mood': 'warm golden daylight',
        'evaluation_focus': 'Red vintage bicycle with flower basket against a plain wall.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'robot-chef-cookies',
        'title': 'The Sweet Circuit',
        'gen_prompt': 'A cute small round silver metallic toy robot wearing a tall white chef hat standing on a clean wooden table holding a freshly baked chocolate chip cookie, bright cheerful room',
        'brief': 'A cute small metallic robot wearing a white chef hat holding a chocolate chip cookie on a table.',
        'visual_goals': 'Cute metallic robot, white chef hat, holding a chocolate chip cookie, clean wooden table.',
        'inspiration_keywords': ['Cute Robot', 'White Chef Hat', 'Chocolate Chip Cookie', 'Wooden Table'],
        'key_subjects': ['metallic toy robot', 'white chef hat', 'chocolate chip cookie', 'wooden table'],
        'action': 'holding a chocolate chip cookie',
        'lighting_mood': 'bright clean daylight',
        'evaluation_focus': 'Cute metallic robot wearing a chef hat holding a cookie.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'cozy-fireplace-cat',
        'title': 'Hearthside Slumber',
        'gen_prompt': 'A cute orange tabby kitten curled up fast asleep on a soft cream knitted blanket on a wooden floor in front of a warm stone fireplace with gentle glowing fire logs, warm amber glow',
        'brief': 'A cute orange tabby kitten sleeping curled up on a soft knitted blanket on a wooden floor by a warm fireplace.',
        'visual_goals': 'Sleeping orange kitten curled in a ball, cream knitted blanket, wooden floor, warm fireplace glow.',
        'inspiration_keywords': ['Orange Tabby Kitten', 'Sleeping Cat', 'Knitted Blanket', 'Warm Hearth'],
        'key_subjects': ['orange tabby kitten', 'knitted blanket', 'wooden floor', 'fireplace'],
        'action': 'sleeping peacefully on the blanket',
        'lighting_mood': 'warm cozy amber fireplace glow',
        'evaluation_focus': 'Sleeping orange kitten on a knitted blanket in front of a fireplace.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'panda-eating-bamboo',
        'title': 'The Verdant Sanctuary',
        'gen_prompt': 'A fluffy giant panda bear sitting comfortably upright on fresh green grass holding and eating a green bamboo stalk, clean natural daytime lighting, green bamboo background',
        'brief': 'A fluffy giant panda sitting on green grass eating a fresh green bamboo stalk.',
        'visual_goals': 'Fluffy giant panda sitting upright, holding green bamboo stalk, lush green grass.',
        'inspiration_keywords': ['Giant Panda', 'Green Bamboo Stalk', 'Green Grass', 'Peaceful'],
        'key_subjects': ['giant panda', 'green bamboo stalk', 'green grass'],
        'action': 'sitting and chewing bamboo',
        'lighting_mood': 'gentle natural daylight',
        'evaluation_focus': 'Panda bear sitting on grass holding and eating green bamboo.',
        'is_active': True,
        'created_by': 'system'
    },
    {
        'id': 'sailboat-turquoise-sea',
        'title': 'Azure Drift',
        'gen_prompt': 'A modern sleek white sailboat with hoisted white sails gliding across calm crystal-clear turquoise ocean water under a sunny bright blue sky, clean minimalist maritime view',
        'brief': 'A sleek white sailboat with full white sails sailing on calm clear turquoise ocean water under a sunny blue sky.',
        'visual_goals': 'White hull sailboat with hoisted sails, clear turquoise water, clear blue sky.',
        'inspiration_keywords': ['White Sailboat', 'Hoisted Sails', 'Turquoise Ocean Water', 'Sunny Blue Sky'],
        'key_subjects': ['white sailboat', 'full white sails', 'turquoise ocean water', 'blue sky'],
        'action': 'sailing on calm turquoise sea',
        'lighting_mood': 'bright midday tropical sunshine',
        'evaluation_focus': 'White sailboat with sails on calm turquoise water.',
        'is_active': True,
        'created_by': 'system'
    }
]

os.makedirs('static/images/challenges', exist_ok=True)

clean_challenges = []
for idx, ch in enumerate(CHALLENGES):
    cid = ch['id']
    target_path = os.path.join('static', 'images', 'challenges', f'{cid}.jpg')
    print(f'[{idx+1}/{len(CHALLENGES)}] Generating clean simple image for: {cid}...')
    
    # Generate fresh clean minimalist image
    try:
        gen = image_generator.generate(ch['gen_prompt'])
        if gen.get('success') and gen.get('image_data'):
            b64_data = gen['image_data'].split('base64,')[1]
            with open(target_path, 'wb') as f:
                f.write(base64.b64decode(b64_data))
            print(f'  ✓ Saved {target_path} ({len(b64_data)} bytes)')
        else:
            print(f"  ✗ Failed to generate image: {gen.get('error')}")
    except Exception as e:
        print(f'  ✗ Error: {e}')
    
    # Save clean challenge dict (without gen_prompt)
    clean_dict = dict(ch)
    clean_dict.pop('gen_prompt', None)
    clean_challenges.append(clean_dict)
    time.sleep(1)

with open('challenges.json', 'w', encoding='utf-8') as f:
    json.dump(clean_challenges, f, indent=2)

with open('data/challenges.json', 'w', encoding='utf-8') as f:
    json.dump(clean_challenges, f, indent=2)

print('All 16 simplified challenges generated and saved successfully!')
