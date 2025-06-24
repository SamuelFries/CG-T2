# ***********************************************************************************
#   OpenGLBasico3D-V5.py
#       Autor: Márcio Sarroglia Pinho
#       pinho@pucrs.br
#   Este programa exibe dois Cubos em OpenGL
#   Para maiores informações, consulte
# 
#   Para construir este programa, foi utilizada a biblioteca PyOpenGL, disponível em
#   http://pyopengl.sourceforge.net/documentation/index.html
#
#   Outro exemplo de código em Python, usando OpenGL3D pode ser obtido em
#   http://openglsamples.sourceforge.net/cube_py.html
#
#   Sugere-se consultar também as páginas listadas
#   a seguir:
#   http://bazaar.launchpad.net/~mcfletch/pyopengl-demo/trunk/view/head:/PyOpenGL-Demo/NeHe/lesson1.py
#   http://pyopengl.sourceforge.net/documentation/manual-3.0/index.html#GLUT
#
#   No caso de usar no MacOS, pode ser necessário alterar o arquivo ctypesloader.py,
#   conforme a descrição que está nestes links:
#   https://stackoverflow.com/questions/63475461/unable-to-import-opengl-gl-in-python-on-macos
#   https://stackoverflow.com/questions/6819661/python-location-on-mac-osx
#   Veja o arquivo Patch.rtf, armazenado na mesma pasta deste fonte.
# 
# ***********************************************************************************
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from Ponto import Ponto

from ListaDeCoresRGB import *
import Texture as TEX

#from PIL import Image
import math
import time
import random as ALE

import numpy as np
from PIL import Image


Angulo = 0.0

# Quantidade de ladrilhos do piso (inicializada em algum ponto no cadigo)
QtdX = 0
QtdZ = 0

AlturaViewportDeMensagens = 0.2
AnguloDeVisao = 90.0


# Representa o conteúdo de uma celula do piso
class Elemento:
    def __init__(self, tipo=0, cor_do_objeto=0, cor_do_piso=0, altura=0.0, texture_id=0):
        self.tipo = tipo
        self.cor_do_objeto = cor_do_objeto
        self.cor_do_piso = cor_do_piso
        self.altura = altura
        self.texture_id = texture_id


# Codigos que definem o tipo do elemento que está em uma calula
VAZIO = 0
PREDIO = 10
RUA = 20
COMBUSTIVEL = 30
VEICULO = 40

# Matriz que armazena informações sobre o que existe na cidade
Cidade = [[Elemento() for _ in range(100)] for _ in range(100)]

# Pontos de interesse
Observador = Ponto()
Alvo = Ponto()
TerceiraPessoa = Ponto()
PosicaoVeiculo = Ponto()

# Variáveis do veículo
VeiculoX = 1.0  # Posição X do veículo no grid
VeiculoZ = 1.0  # Posição Z do veículo no grid
VeiculoAngulo = 0.0  # Ângulo de rotação do veículo (0=Norte, 90=Leste, 180=Sul, 270=Oeste)
VeiculoDirecao = 0.0  # Direção de movimento (pode ser diferente da orientação visual)
VelocidadeVeiculo = 0.1  # Velocidade de movimento
VeiculoEmMovimento = False  # Controla se o veículo está se movendo automaticamente

ComTextura = 0


# **********************************************************************
#
# # **********************************************************************
def ImprimeCidade():
    for i in range(QtdZ):
        for j in range(QtdX):
            print(Cidade[i][j].cor_do_piso, end=" ")
        print()
        

# **********************************************************************
# def InicializaCidade(qtd_x, qtd_z):
# Esta função será substituída por uma que lê a matriz que representa
# a cidade
# **********************************************************************
def InicializaCidade(qtd_x, qtd_z):
    LeMatrizCidade("Cidade.txt")
    #ImprimeCidade()

def LeMatrizCidade(nome_arquivo):
    global Cidade, QtdX, QtdZ
    with open(nome_arquivo, "r") as f:
        linhas = f.readlines()
        QtdZ = len(linhas)
        QtdX = len(linhas[0].split())
        for i, linha in enumerate(linhas):
            valores = linha.strip().split()
            for j, val in enumerate(valores):
                valor = int(val)
                if valor >= PREDIO and valor < RUA:
                    Cidade[i][j].tipo = PREDIO
                    Cidade[i][j].cor_do_piso = (
                        ALE.uniform(0.5, 1.0),
                        ALE.uniform(0.5, 1.0),
                        ALE.uniform(0.5, 1.0)
                    )
                    if valor < 17:
                        Cidade[i][j].altura = 0  # Sem prédio
                    else:
                        Cidade[i][j].altura = (valor - PREDIO) / 4 + 2.0 # altura mínima 2.0, por exemplo

                elif valor == RUA:
                    Cidade[i][j].tipo = RUA
                    Cidade[i][j].cor_do_piso = (0,0,0)  # Black
                    Cidade[i][j].altura = 0
                
                elif valor == COMBUSTIVEL:
                    Cidade[i][j].tipo = COMBUSTIVEL
                    Cidade[i][j].cor_do_piso = (1,1,0)  # Yellow
                    Cidade[i][j].altura = 0
                elif valor == VEICULO:
                    Cidade[i][j].tipo = VEICULO
                    Cidade[i][j].cor_do_piso = (1,0,0)  # Red
                    Cidade[i][j].altura = 0
                else:
                    Cidade[i][j].tipo = VAZIO
                    Cidade[i][j].cor_do_piso = (1,1,1)  # White
                    Cidade[i][j].altura = 0

                    
# **********************************************************************
# def posiciona_em_terceira_pessoa():
#   Este método posiciona o observador fora do cenário, olhando para o
#   centro do mapa (ou para o veículo)
# As variáveis "TerceiraPessoa" e "PosicaoVeiculo" são setadas na INIT
# **********************************************************************
def posiciona_em_terceira_pessoa():
    global Observador, Alvo
    Observador = Ponto(TerceiraPessoa.x, TerceiraPessoa.y, TerceiraPessoa.z)  # Posiciona observador
    Alvo = Ponto(PosicaoVeiculo.x, PosicaoVeiculo.y, PosicaoVeiculo.z)        # Define alvo como o veículo

    Alvo.imprime("Posiciona - Veiculo:") 
    
      
# **********************************************************************
#  init()
#  Inicializa os parametros globais de OpenGL
#/ **********************************************************************
def init():
    global QtdX, QtdZ
    global TerceiraPessoa, PosicaoVeiculo
    global AnguloDeVisao

    glClearColor(0.0, 0.0, 1.0, 1.0)  # Fundo de tela amarelo
    
    glClearDepth(1.0)
    glDepthFunc(GL_LESS)

    glShadeModel(GL_SMOOTH)  # Ou GL_FLAT, se desejar
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

    glEnable(GL_DEPTH_TEST)   # Ativa teste de profundidade
    #glEnable(GL_CULL_FACE)    # Ativa remoção de faces traseiras    

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glEnable(GL_NORMALIZE)  # Normaliza vetores normais

    # Quantidade de retângulos do piso vai depender do mapa (hardcoded aqui)
    QtdX = 20
    QtdZ = 20

    InicializaCidade(QtdX, QtdZ)    # ImprimeCidade()

    # Define a posição do observador e do veículo com base no tamanho do mapa
    TerceiraPessoa = Ponto(QtdX / 2, 10, QtdZ * 1.1)
    PosicaoVeiculo = Ponto(QtdX / 2, 0, QtdZ / 2)

    # Inicializa a posição do veículo em uma rua válida
    # Procura uma posição inicial válida (rua)
    for i in range(QtdZ):
        for j in range(QtdX):
            if Cidade[i][j].tipo == RUA:
                VeiculoX = j + 0.5  # Centro da célula
                VeiculoZ = i + 0.5  # Centro da célula
                VeiculoAngulo = 0.0  # Olhando para o norte
                PosicaoVeiculo.x = VeiculoX
                PosicaoVeiculo.z = VeiculoZ
                break
        else:
            continue
        break

    posiciona_em_terceira_pessoa()

    TEX.LoadTexture("bricks.jpg") # esta serah a textura 0
    TEX.LoadTexture("Piso.jpg")   # esta serah a textura 1
    TEX.LoadTexture("Asfalto.jpg") # esta serah a textura 2


    #image = Image.open("Tex.png")
    #print ("X:", image.size[0])
    #print ("Y:", image.size[1])
    #image.show()
    AnguloDeVisao = 90


# **********************************************************************
#
# **********************************************************************
def DesenhaPredio(altura, cor):
    glPushMatrix()
    glTranslatef(0, altura/2, 0)
    glScalef(0.2, altura, 0.2)
    glColor3f(*cor)  # Define a cor do prédio
    glutSolidCube(1)
    glPopMatrix()

# **********************************************************************
# def DesenhaLadrilhoTEX(id_textura):
# Desenha uma célula do piso aplciando a textura ativa.
# **********************************************************************
def DesenhaLadrilhoTEX(id_textura):

    # Seta a cor como branco pois vai desenha com textura
    glColor3f(1, 1, 1)   

    # Habilita a textura id_textura
    TEX.UseTexture(id_textura)

    # Desenha o poligono
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-0.5, 0.0, -0.5)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-0.5, 0.0, 0.5)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(0.5, 0.0, 0.5)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(0.5, 0.0, -0.5)
    glEnd()

    # Deasabilita a textura
    TEX.UseTexture(-1)


# **********************************************************************
# DesenhaPoligonosComTextura()
# **********************************************************************
def DesenhaPoligonosComTextura():

    pass #Não desenha nada 

# **********************************************************************
# void DesenhaLadrilho(int corBorda, int corDentro)
# Desenha uma celula do piso.
# O ladrilho tem largula 1, centro no (0,0,0) e esta sobre o plano XZ
# **********************************************************************
def DesenhaLadrilho(corBorda, corDentro):
    glColor3f(0,0,1) # desenha QUAD preenchido
    defineCor(corDentro)
    glBegin ( GL_QUADS )
    glNormal3f(0,1,0)
    glVertex3f(-0.5,  0.0, -0.5)
    glVertex3f(-0.5,  0.0,  0.5)
    glVertex3f( 0.5,  0.0,  0.5)
    glVertex3f( 0.5,  0.0, -0.5)
    glEnd()

    
    glColor3f(1,1,1) # desenha a borda da QUAD 
    defineCor(corBorda)
    glLineWidth(3)
    glBegin ( GL_LINE_STRIP )
    glNormal3f(0,1,0)
    glVertex3f(-0.5,  0.0, -0.5)
    glVertex3f(-0.5,  0.0,  0.5)
    glVertex3f( 0.5,  0.0,  0.5)
    glVertex3f( 0.5,  0.0, -0.5)
    glEnd()
    glLineWidth(1)
    
# **********************************************************************
#
# **********************************************************************  
def DesenhaCidade(QtdX, QtdZ):
    ALE.seed(100)
    glPushMatrix()

    for x in range(QtdX):
        glPushMatrix()
        for z in range(QtdZ):
            celula = Cidade[z][x]
            if celula.tipo == RUA:
                DesenhaLadrilhoTEX(2)  # Usa a textura de rua (ajuste o índice se necessário)
            else:
                DesenhaLadrilhoTEX(1)
                if celula.tipo == PREDIO:
                    glPushMatrix()
                    DesenhaPredio(celula.altura, celula.cor_do_piso)
                    glPopMatrix()
            glTranslated(0, 0, 1)
        glPopMatrix()
        glTranslated(1, 0, 0)

    glPopMatrix()

# **********************************************************************
def DefineLuz():
    # Define cores para um objeto dourado
    LuzAmbiente = [0.4, 0.4, 0.4] 
    LuzDifusa   = [0.7, 0.7, 0.7]
    LuzEspecular = [0.9, 0.9, 0.9]
    #PosicaoLuz0  = [2.0, 3.0, 0.0 ]  # PosiÃ§Ã£o da Luz
    PosicaoLuz0  = [Alvo.x, Alvo.y, Alvo.z]
    Especularidade = [1.0, 1.0, 1.0]

    # ****************  Fonte de Luz 0

    glEnable ( GL_COLOR_MATERIAL )

    #Habilita o uso de iluminaÃ§Ã£o
    glEnable(GL_LIGHTING)

    #Ativa o uso da luz ambiente
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, LuzAmbiente)
    # Define os parametros da luz numero Zero
    glLightfv(GL_LIGHT0, GL_AMBIENT, LuzAmbiente)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, LuzDifusa  )
    glLightfv(GL_LIGHT0, GL_SPECULAR, LuzEspecular  )
    glLightfv(GL_LIGHT0, GL_POSITION, PosicaoLuz0 )
    glEnable(GL_LIGHT0)

    # Ativa o "Color Tracking"
    glEnable(GL_COLOR_MATERIAL)

    # Define a reflectancia do material
    glMaterialfv(GL_FRONT,GL_SPECULAR, Especularidade)

    # Define a concentraÃ§Ã£o do brilho.
    # Quanto maior o valor do Segundo parametro, mais
    # concentrado sera o brilho. (Valores validos: de 0 a 128)
    glMateriali(GL_FRONT,GL_SHININESS,51)


# **********************************************************************
#
# **********************************************************************
def PosicUser():
    global AspectRatio
    # Salva o tamanho da janela
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Seta a viewport para ocupar toda a janela
    # glViewport(0, 0, w, h)
    #
    # glViewport(0, int(h * AlturaViewportDeMensagens), w, int(h - h * AlturaViewportDeMensagens))

    #print ("AspectRatio", AspectRatio)
    AspectRatio = w / h
    gluPerspective(AnguloDeVisao,AspectRatio,0.01,1500) # Projecao perspectiva

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(Observador.x, Observador.y, Observador.z,   # Posição do Observador
              Alvo.x, Alvo.y, Alvo.z,                      # Posição do Alvo
              0.0, 1.0, 0.0)                               # Vetor UP

# **********************************************************************
#  reshape( w: int, h: int )
#  trata o redimensionamento da janela OpenGL
# **********************************************************************
def reshape(w: int, h: int):
    global AspectRatio
	# Evita divisÃ£o por zero, no caso de uma janela com largura 0.
    if h == 0:
        h = 1
    # Ajusta a relacao entre largura e altura para evitar distorcao na imagem.
    # Veja funcao "PosicUser".
    
	# Reset the coordinate system before modifying
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Seta a viewport para ocupar toda a janela
    glViewport(0, 0, w, h)
    
    # Ajusta a viewport para ocupar a parte superior da janela
    glViewport(0, int(h * AlturaViewportDeMensagens), w, int(h - h * AlturaViewportDeMensagens))

    AspectRatio = w / h
    gluPerspective(AnguloDeVisao,AspectRatio,0.01,1500) # Projecao perspectiva
    # PosicUser()

# **********************************************************************
# Imprime o texto S na posicao (x,y), com a cor 'cor'
# **********************************************************************
def PrintString(S: str, x: int, y: int, cor: tuple):
    defineCor(cor) 
    glRasterPos3f(x, y, 0) # define posicao na tela
    
    for c in S:
        # GLUT_BITMAP_HELVETICA_10
        # GLUT_BITMAP_TIMES_ROMAN_24
        # GLUT_BITMAP_HELVETICA_18
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))


# **********************************************************************
# Imprime as coordenadas do ponto P na posicao (x,y), com a cor 'cor'
# **********************************************************************
def ImprimePonto(P: Ponto, x: int, y: int, cor: tuple):
    S = f'({P.x:.2f}, {P.y:.2f})'
    PrintString(S, x, y, cor)

# **********************************************************************
# Esta funcao cria uam area 2D para escrever mensagens de texto na tela
# **********************************************************************
def DesenhaEm2D():
    ativar_luz = False

    if glIsEnabled(GL_LIGHTING):
        glDisable(GL_LIGHTING)
        ativar_luz = True

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    # Salva o tamanho da janela
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)

    # Define a área a ser ocupada pela mensagens dentro da Janela
    glViewport(0, 0, w, int(h * AlturaViewportDeMensagens))  # janela de mensagens fica na parte de baixo

    # Define os limites lógicos da área OpenGL dentro da janela
    glOrtho(0, 10, 0, 10, 0, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Desenha linha que divide as áreas 2D e 3D
    defineCor(GreenCopper)
    glLineWidth(10)
    glBegin(GL_LINES)
    glVertex2f(0, 3)
    glVertex2f(10, 3)
    glEnd()

    # PrintString("Esta area eh destinada a mensagens de texto. Veja a funcao DesenhaEm2D", 0, 8, White)

    PrintString("Gasolina", 0, 0, Orange)  # Orange
    PrintString("100", 2, 0, Orange)  # Orange
    
    # Status do veículo
    status = "Movendo" if VeiculoEmMovimento else "Parado"
    PrintString(f"Veiculo: {status}", 0, 2, Orange)  # Orange
    PrintString("Espaco: Liga/Desliga movimento", 0, 1, Orange)  # Orange

    # Restaura os parâmetros que foram alterados
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, int(h * AlturaViewportDeMensagens), w, int(h - h * AlturaViewportDeMensagens))

    if ativar_luz:
        glEnable(GL_LIGHTING)

# **********************************************************************
# DesenhaCubo()
# Desenha o cenario
# **********************************************************************
def DesenhaCubo():
    glutSolidCube(1)


# **********************************************************************
# display()
# Funcao que exibe os desenhos na tela
# **********************************************************************
def display():
    global Angulo
    # Limpa a tela com  a cor de fundo
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    DefineLuz()
    PosicUser()
    glMatrixMode(GL_MODELVIEW)
    
    glPushMatrix()
    DesenhaCidade(QtdX,QtdZ)
    glPopMatrix()

    glPushMatrix()
    DesenhaVeiculo()
    glPopMatrix()

    glPushMatrix()
    DesenhaPoligonosComTextura()
    glPopMatrix()

    DesenhaEm2D()    

    Angulo = Angulo + 1

    glutSwapBuffers()


# **********************************************************************
# animate()
# Funcao chama enquanto o programa esta ocioso
# Calcula o FPS e numero de interseccao detectadas, junto com outras informacoes
#
# **********************************************************************
# Variaveis Globais
nFrames, TempoTotal, AccumDeltaT = 0, 0, 0
oldTime = time.time()

def animate():
    global nFrames, TempoTotal, AccumDeltaT, oldTime

    nowTime = time.time()
    dt = nowTime - oldTime
    oldTime = nowTime

    AccumDeltaT += dt
    TempoTotal += dt
    nFrames += 1
    
    if AccumDeltaT > 1.0/30:  # fixa a atualizacao da tela em 30
        AccumDeltaT = 0
        AtualizaMovimentoVeiculo()  # Atualiza o movimento do veículo
        glutPostRedisplay()


# **********************************************************************
#  keyboard ( key: int, x: int, y: int )
#
# **********************************************************************
ESCAPE = b'\x1b'
def keyboard(*args):
    global image, ComTextura
    #print (args)
    # If escape is pressed, kill everything.

    if args[0] == ESCAPE:   # Termina o programa qdo
        os._exit(0)         # a tecla ESC for pressionada

    if args[0] == b't' :
        ComTextura = 1 - ComTextura

    if args[0] == b' ':  # Barra de espaço
        AlternaMovimentoVeiculo()

    # ForÃ§a o redesenho da tela
    glutPostRedisplay()

# **********************************************************************
# VerificaPosicaoValida()
# Verifica se uma posição é válida para o veículo (deve ser rua)
# **********************************************************************
def VerificaPosicaoValida(x, z):
    # Verifica se está dentro dos limites do mapa
    if x < 0 or x >= QtdX or z < 0 or z >= QtdZ:
        return False
    
    # Verifica se a posição é uma rua
    return Cidade[int(z)][int(x)].tipo == RUA

# **********************************************************************
# DesenhaVeiculo()
# Desenha o veículo como um triângulo
# **********************************************************************
def DesenhaVeiculo():
    glPushMatrix()
    glTranslatef(VeiculoX, 0.1, VeiculoZ)  # Altura 0.1 para ficar acima do chão
    glRotatef(VeiculoAngulo, 0, 1, 0)
    glColor3f(1.0, 0.0, 0.0)  # Vermelho

    # Corpo da seta (base do prisma)
    glBegin(GL_QUADS)
    # Base inferior
    glVertex3f(-0.1, 0.0, -0.15)
    glVertex3f( 0.1, 0.0, -0.15)
    glVertex3f( 0.1, 0.0,  0.15)
    glVertex3f(-0.1, 0.0,  0.15)
    # Base superior
    glVertex3f(-0.1, 0.1, -0.15)
    glVertex3f( 0.1, 0.1, -0.15)
    glVertex3f( 0.1, 0.1,  0.15)
    glVertex3f(-0.1, 0.1,  0.15)
    # Lados
    glVertex3f(-0.1, 0.0, -0.15)
    glVertex3f(-0.1, 0.1, -0.15)
    glVertex3f(-0.1, 0.1,  0.15)
    glVertex3f(-0.1, 0.0,  0.15)

    glVertex3f(0.1, 0.0, -0.15)
    glVertex3f(0.1, 0.1, -0.15)
    glVertex3f(0.1, 0.1,  0.15)
    glVertex3f(0.1, 0.0,  0.15)

    glVertex3f(-0.1, 0.0, -0.15)
    glVertex3f( 0.1, 0.0, -0.15)
    glVertex3f( 0.1, 0.1, -0.15)
    glVertex3f(-0.1, 0.1, -0.15)

    glVertex3f(-0.1, 0.0, 0.15)
    glVertex3f( 0.1, 0.0, 0.15)
    glVertex3f( 0.1, 0.1, 0.15)
    glVertex3f(-0.1, 0.1, 0.15)
    glEnd()

    # Ponta da seta (pirâmide)
    glBegin(GL_TRIANGLES)
    # Frente
    glVertex3f( 0.0, 0.15, 0.35)  # ponta superior
    glVertex3f(-0.15, 0.0, 0.15)
    glVertex3f( 0.15, 0.0, 0.15)
    # Lado esquerdo
    glVertex3f( 0.0, 0.15, 0.35)
    glVertex3f(-0.1, 0.0, -0.15)
    glVertex3f(-0.15, 0.0, 0.15)
    # Lado direito
    glVertex3f( 0.0, 0.15, 0.35)
    glVertex3f( 0.1, 0.0, -0.15)
    glVertex3f( 0.15, 0.0, 0.15)
    # Base traseira
    glVertex3f( 0.0, 0.15, 0.35)
    glVertex3f(-0.1, 0.0, -0.15)
    glVertex3f( 0.1, 0.0, -0.15)
    glEnd()

    glPopMatrix()

# **********************************************************************
# MoveVeiculo()
# Move o veículo na direção atual se a posição for válida
# **********************************************************************
def MoveVeiculo(direcao):
    global VeiculoX, VeiculoZ, VeiculoAngulo

    ang_rad = math.radians(VeiculoAngulo)
    dx = math.sin(ang_rad)
    dz = -math.cos(ang_rad)

    if direcao == "frente":
        nova_x = VeiculoX + dx * VelocidadeVeiculo
        nova_z = VeiculoZ + dz * VelocidadeVeiculo
    elif direcao == "tras":
        nova_x = VeiculoX - dx * VelocidadeVeiculo
        nova_z = VeiculoZ - dz * VelocidadeVeiculo
    else:
        nova_x, nova_z = VeiculoX, VeiculoZ

    if VerificaPosicaoValida(nova_x, nova_z):
        VeiculoX = nova_x
        VeiculoZ = nova_z
        PosicaoVeiculo.x = VeiculoX
        PosicaoVeiculo.z = VeiculoZ
        posiciona_em_terceira_pessoa()

def RotacionaVeiculo(direcao):
    global VeiculoAngulo
    if direcao == "esquerda":
        VeiculoAngulo = (VeiculoAngulo - 90) % 360
    elif direcao == "direita":
        VeiculoAngulo = (VeiculoAngulo + 90) % 360
    posiciona_em_terceira_pessoa()

# **********************************************************************
#  arrow_keys ( a_keys: int, x: int, y: int )   
# **********************************************************************

def arrow_keys(a_keys: int, x: int, y: int):
    #if a_keys == GLUT_KEY_UP:         # Se pressionar UP
    #    MoveVeiculo("frente")
    #if a_keys == GLUT_KEY_DOWN:       # Se pressionar DOWN
    #    MoveVeiculo("tras")
    if a_keys == GLUT_KEY_LEFT:       # Se pressionar LEFT
        RotacionaVeiculo("esquerda")
    if a_keys == GLUT_KEY_RIGHT:      # Se pressionar RIGHT
        RotacionaVeiculo("direita")

    glutPostRedisplay()

def mouse(button: int, state: int, x: int, y: int):
    glutPostRedisplay()

def mouseMove(x: int, y: int):
    glutPostRedisplay()

# **********************************************************************
# AlternaMovimentoVeiculo()
# Liga/desliga o movimento automático do veículo
# **********************************************************************
def AlternaMovimentoVeiculo():
    global VeiculoEmMovimento
    VeiculoEmMovimento = not VeiculoEmMovimento

# **********************************************************************
# AtualizaMovimentoVeiculo()
# Atualiza a posição do veículo se estiver em movimento
# **********************************************************************
def AtualizaMovimentoVeiculo():
    if VeiculoEmMovimento:
        MoveVeiculo("frente")

# ***********************************************************************************
# Programa Principal
# ***********************************************************************************


glutInit(sys.argv)
glutInitDisplayMode(GLUT_RGBA|GLUT_DEPTH | GLUT_RGB)
glutInitWindowPosition(0, 0)

# Cria a janela na tela, definindo o nome da
# que aparecera na barra de ti­tulo da janela.
glutInitWindowPosition(0, 0)
# Define o tamanho inicial da janela grafica do programa
glutInitWindowSize(900, 700)
wind = glutCreateWindow(b"Simulador de Cidade")


# executa algumas inicializacoes
init ()

# Define que o tratador de evento para
# o redesenho da tela. A funcao "display"
# sera chamada automaticamente quando
# for necessario redesenhar a janela
glutDisplayFunc(display)
glutIdleFunc (animate)

# o redimensionamento da janela. A funcao "reshape"
# Define que o tratador de evento para
# sera chamada automaticamente quando
# o usuario alterar o tamanho da janela
glutReshapeFunc(reshape)

# Define que o tratador de evento para
# as teclas. A funcao "keyboard"
# sera chamada automaticamente sempre
# o usuario pressionar uma tecla comum
glutKeyboardFunc(keyboard)
    
# Define que o tratador de evento para
# as teclas especiais(F1, F2,... ALT-A,
# ALT-B, Teclas de Seta, ...).
# A funcao "arrow_keys" sera chamada
# automaticamente sempre o usuario
# pressionar uma tecla especial
glutSpecialFunc(arrow_keys)

#glutMouseFunc(mouse)
#glutMotionFunc(mouseMove)


try:
    # inicia o tratamento dos eventos
    glutMainLoop()
except SystemExit:
    pass
