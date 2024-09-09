import random as rand

DISPENSERS = 4
FUNGUS_PROD_CHANCE = 0.08496
FOLIAGE_PROD_CHANCE = 0.79502
FUNGUS_GROWTH_CHANCE = 0.4
TICKS_PH = 72000

print("Rates if growth dispenser triggers first")
for cycles in range(1, 6):
    fungi_grown = 0
    elapsed_gt = 0
    i = 0
    for i in range(int(1e8)):
        has_genned = False
        for c in range(cycles):
            elapsed_gt += 4
            # fungus growth dispenser triggers
            if has_genned:
                if rand.random() < 1 - (1 - FUNGUS_GROWTH_CHANCE) ** DISPENSERS:
                    fungi_grown += 1
                    break

            # nylium dispenser triggers
            if not has_genned:
                plant = rand.random()
                if plant < FUNGUS_PROD_CHANCE:
                    has_genned = True
                elif plant > FUNGUS_PROD_CHANCE and plant < FOLIAGE_PROD_CHANCE + FUNGUS_PROD_CHANCE:
                    # If foliage genned then gg for next cycles
                    elapsed_gt += 4 * (cycles - (c + 1)) 
                    break

    
    print("Cycles:", cycles)
    print("Fungi grown/h:", fungi_grown * TICKS_PH / elapsed_gt)
    print()