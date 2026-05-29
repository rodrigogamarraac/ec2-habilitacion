## Logica


Bueno cree otro archivo en `api/v1` llamado `restaurants` , cree 2 endpoints, una el filter allergens y otro para conseguir todos los Restaurants.

Solicito que primero se corra el endopoint para llamar a todos los restaurants y se copie el Id del restaurante al endpoint de filter allergens.

`http://localhost/api/v1/restaurants/`

`http://localhost/api/v1/restaurants/{id}/menu?date=2026-05-23&exclude_allergens=cacao,Res`

`Fecha en formato YYYY-MM-DD`

Bueno lo que hice fue agarrar la lógica del servicio `GetMenu`, pero esta vez en vez de traer todos los menus de todos los restaurantes, trae solo el del restaurante que se paso el Id.

Luego cree el archivo `services/getMenuFilter`.


Luego de eso, como tuve la dificultad con el ORM, decidi hacerlo despues que trajo todos los menus de el restaurante en especifico, una vez los trae, hago un ciclo for para acceder a todos los MenuItems de la lista, entro a la lista de ingredientes, la transformo en array, para recorrerla, porque en mi modelo los ingredientes son string plano, y verifico que ninguno de los ingredientes este en la lista pasado por el endpoint `exclude_allergens`, y si hay alguno, no se lo incluye en la lista final, y si no hay, se agrega.

Y ya si el usuario no le pasa los `exclude_allergens`, la peticion trae todos los MenuItems de ese restaurante

Basicamente lo hice asi, porque se me dificulto hacer la consulta con el ORM, y las relaciones se me dificultaban, pero lo pude solucionar con el buen ciclo for, y la lista comprimida.

Lo que falto fue, guardarlo en cache, intente guardarlo, pero las keys se me repetian, asi que los datos eran inconsistentes, trate de hacerlo con variables dinamicas, como datetime.today o asi, pero no servia, tambien el 2do endpoint que se me dio en la orden no lo hice, ya que mi diseño de la base de datos no tiene un `course` como tal, no tiene un tipo de comida, asi que ahi me quede en blanco.