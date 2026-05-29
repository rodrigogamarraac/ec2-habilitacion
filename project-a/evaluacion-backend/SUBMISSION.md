# Submission

## Lo que mas me enorgullece

Lo que mas me enorgullece es como quedo estructurado el servicio de FastAPI. Separe la arquitectura por capas (routers, servicios, repositorios) y a usar interfaces con Protocol para que cada parte sea independiente. 

## Lo que menos me satisface

La invalidacion de cache. Ahora mismo la cache de Redis vence cada 60 segundos, lo que significa que si alguien cambia algo en el admin de Django, la API puede mostrar datos viejos. Lo mejor seria que al guardar en el admin se borrara automaticamente la clave de Redis usando (post_save/post_delete). No lo hice por cuestiones de tiempo y por desconocer como implementarlo correctamente.
