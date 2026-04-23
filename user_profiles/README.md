# User Profiles

Ogni file in questa cartella corrisponde a un utente Discord identificato dal suo `user_id`.

## Struttura
```
user_profiles/
  <discord_user_id>.json   — profilo e account collegati dell'utente
  README.md                — questo file
```

## Regole
- Craw crea il profilo al primo contatto con un nuovo utente
- Ogni utente può collegare i propri account (Google, GitHub, ecc.) solo per sé stesso
- Le credenziali di un utente non sono mai usate per un altro
- Diego (owner) ha accesso completo a tutti i profili per scopi di amministrazione
- Gli utenti normali vedono e modificano solo il proprio profilo
