
""""
#                                   função
def soma10(numero):
    numero = int(numero)
    numero = numero + 10
    return numero

#                                   programa principal
n = input("Digite um numero: ")
n = soma10(n)
print('Numero acrescido de 10: %d.' %n)
"""
n = int()
def fatorial(n):
    fat = 1
    for i in range (2, n+1):
        fat = fat * i
    return fat

x = int(input("Numero : "))
print("fatorial : %d" % fatorial (x))
print(n)