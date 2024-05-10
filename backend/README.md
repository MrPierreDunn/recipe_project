# ViewSets

Русурсы: 

Пользователи

### api/users

GET api/users - получить список пользователей  
GET api/users/{id} - получить пользователя с id  
POST api/users - создать пользователя  
PUT api/users/{id} - изменить пользователя с id  
DELETE api/users/{id} - удалить пользователя с id  

Тэги

### api/tags

GET api/tags - получить список тегов  
GET api/tags/{id} - получить тег по ID  

Рецепты

### api/recipes


GET api/recipes - получить список рецептов  
GET api/recipes/{id} - получить рецепт с id  
POST api/recipes - создать рецепт  
PUT api/recipes/{id} - изменить рецепт с id  
DELETE api/recipes/{id} - удалить рецепт с id  


GET api/recipes/download_shopping_cart - получить список покупок  
POST api/recipes/{id}/shopping_cart - добавить в список покупок  
DELETE api/recipes/{id}/shopping_cart - удалить из списка покупок  


POST api/recipes/{id}/favorite - добавить рецепт в избранное  
DELETE api/recipes/{id}/favorite - удалить рецепт из избранного  



Ингрединты

### api/ingredients

GET api/ingredients - получить список ингредиентов  
GET api/ingredients/{id} - получить ингредиент по ID 

# Pagination


http://localhost/api/users/subscriptions/?page=1&limit=5&recipes_limit=10

?page=1&limit=5&recipes_limit=10 - доступ к ним через self.kwargs или self.request.kwargs

Нужно писать serializer_method_fields для subscribishion  
Recipe.objects.filter(author=ЧТО-ТО)[:recipes_limit] # можно так  


# Serializers


# Authentication