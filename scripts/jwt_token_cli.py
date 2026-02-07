import jwt, time
secret='dev-secret-change-me'
payload={'sub':'demo','aud':'agentic-commerce','scope':'wallet:read wallet:write wallet:admin','exp':int(time.time())+3600}
print(jwt.encode(payload, secret, algorithm='HS256'))
