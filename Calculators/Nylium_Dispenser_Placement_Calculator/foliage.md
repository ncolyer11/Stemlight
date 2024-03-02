```java
for (int k = 0; k < 9; ++k) {
    BlockPos blockPos2 = blockPos.add(
        random.nextInt(2) - random.nextInt(2),
        random.nextInt(2) - random.nextInt(2)
    );
    BlockState blockState2 = netherForestVegetationFeatureConfig.stateProvider.get(random, blockPos2); // weighted call to get foliage

    // if(is valid block check)

    //sets block;
    ++j;
}
```