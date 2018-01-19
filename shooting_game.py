import os, pygame, random, math
from collections import deque
from pygame.locals import *
from pygame.compat import geterror


main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')

direction = {None:(0,0), K_w:(0,-1), K_s:(0,1), K_a:(-1,0), K_d:(1,0)}

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()
     
class Explosion(pygame.sprite.Sprite):
    def __init__(self, explodedThing, linger=30):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('explosion.png', -1)
        self.rect.center = explodedThing.rect.center 
        self.linger = linger
    
    def update(self):
        self.linger -= 1
        if self.linger <= 0:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, ship):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('missile.png', -1)
        self.rect.midbottom = ship.rect.midtop
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = -4

    def update(self):
        newpos = self.rect.move(0,self.speed)
        if newpos.bottom > self.area.top:
            self.rect = newpos
        else:
            self.kill()
            
class Drawing(object):
    def __init__(self, drawFunc):
        self.drawFunc = drawFunc
    
    def draw(self):
        pass

class Bomb(Drawing):
    def __init__(self, ship):
        Drawing.__init__(self, pygame.draw.circle)
        self.center = ship.rect.center 
        self.radius = 20

    def draw(self):
        self.radius += 4
        self.drawFunc(pygame.display.get_surface(), Color(0,0,255,128), self.center, self.radius, 3)
        if self.center[1] - self.radius <= 0:
            return False
        return True

class Ship(pygame.sprite.Sprite):
    def __init__(self, MisType=Missile, ExplosionType=Explosion):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('ship.png', -1)
        self.screen = pygame.display.get_surface()
        self.area = self.screen.get_rect()
        self.rect.midbottom = (self.screen.get_width()//2, self.area.bottom)
        self.vert = 0
        self.horiz = 0
        self.MisType = MisType
        self.ExplosionType = ExplosionType
        self.alive = True

    def update(self):
        newpos = self.rect.move((self.horiz, self.vert))
        newhoriz = self.rect.move((self.horiz, 0))
        newvert = self.rect.move((0, self.vert))

        if not (newpos.left <= self.area.left
            or newpos.top <= self.area.top
            or newpos.right >= self.area.right
            or newpos.bottom >= self.area.bottom):
            self.rect = newpos
        elif not (newhoriz.left <= self.area.left
            or newhoriz.right >= self.area.right):
            self.rect = newhoriz
        elif not (newvert.top <= self.area.top
            or newvert.bottom >= self.area.bottom):
            self.rect = newvert

    def fire(self):
        return self.MisType(self) 

    def bomb(self):
        return Bomb(self)

    def explode(self):
        self.kill()
        self.alive = False
        return self.ExplosionType(self)

class Alien(pygame.sprite.Sprite):
    def __init__(self, color):
        pygame.sprite.Sprite.__init__(self)
        self.loc = 0
        self.image, self.rect = load_image('space_invader_'+ color +'.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.midtop = (random.randint(
                            self.area.left + self.rect.width//2, 
                            self.area.right - self.rect.width//2), self.area.top)
        self.initialRect = self.rect
        self.speed = 1

    def update(self):
        horiz, vert = self.moveFunc()
        if horiz + self.initialRect.x > 500:
            horiz -= 500 + self.rect.width
        elif horiz + self.initialRect.x < 0 - self.rect.width:
            horiz += 500 + self.rect.width
        self.rect = self.initialRect.move((horiz, self.speed*self.loc + vert))
        self.loc = self.loc + 1

    def explode(self):
        self.kill()
        return Explosion(self)

class Siney(Alien):
    def __init__(self):
        Alien.__init__(self, 'green')
        self.amp = random.randint(self.rect.width, self.area.width//2)
        self.freq = 1/20
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), 0)

class Roundy(Alien):
    def __init__(self):
        Alien.__init__(self, 'red')
        self.amp = random.randint(self.rect.width, 3*self.rect.width)
        self.freq = 1/20
        self.moveFunc = lambda: (self.amp*math.sin(self.loc*self.freq), self.amp*math.cos(self.loc*self.freq))

class Spikey(Alien):
    def __init__(self):
        Alien.__init__(self, 'blue')
        self.slope = random.choice(list(x for x in range(-3,3) if x != 0))
        self.period = random.choice(list(4*x for x in range(3,31)))
        self.moveFunc = lambda: (self.slope*(self.loc % self.period) if self.loc % self.period < self.period // 2 else self.slope*self.period // 2 - self.slope*((self.loc % self.period) - self.period//2), 0)
                
        
def main():
#Initialize everything
    pygame.init()
    screen = pygame.display.set_mode((500,500))
    pygame.display.set_caption('Shooting Game')
    pygame.mouse.set_visible(0)

#Create the background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

#Display the background
    screen.blit(background, (0, 0))
    pygame.display.flip()
    
#Prepare game objects
    clock = pygame.time.Clock()
    ship = Ship(Missile)
    alienTypes = (Siney, Spikey, Roundy)
    aliens = pygame.sprite.Group()
    missiles = pygame.sprite.Group() 
    explosions = pygame.sprite.Group()
    allsprites = pygame.sprite.RenderPlain((ship,))
    drawings = []
    alienTime = 50
    curTime = 0 
    aliensOffScreen = 5

    while ship.alive:
        clock.tick(120)

    #Event Handling
        for event in pygame.event.get():
            if (event.type == QUIT
                or event.type == KEYDOWN 
                and event.key == K_ESCAPE):
                return 
            elif (event.type == KEYDOWN 
                and event.key in direction.keys()):
                ship.horiz += direction[event.key][0] 
                ship.vert += direction[event.key][1] 
            elif (event.type == KEYUP 
                and event.key in direction.keys()):
                ship.horiz -= direction[event.key][0] 
                ship.vert -= direction[event.key][1] 
            elif (event.type == KEYDOWN
                and event.key == K_SPACE):
                newMissile = ship.fire() 
                newMissile.add(missiles, allsprites)
            elif (event.type == KEYDOWN
                and event.key == K_b):
                drawings.append(ship.bomb()) 


    #Collision Detection
        for alien in aliens:
            
            if alien.rect.top > alien.area.bottom:
                alien.kill()
                aliensOffScreen += 1

            for missile in missiles:
                if pygame.sprite.collide_rect(missile, alien):
                    alien.explode().add(allsprites, explosions)
                    missile.kill()
                    
            if pygame.sprite.collide_rect(alien, ship):
                ship.explode().add(allsprites, explosions)

    #Update Aliens
        if curTime <= 0 and aliensOffScreen > 0:
            random.choice(alienTypes)().add(aliens, allsprites)
            aliensOffScreen -= 1
            curTime = alienTime
        elif curTime > 0:
            curTime -= 1

    

    #Update and draw all sprites 
        allsprites.update()
        screen.blit(background, (0,0))
        allsprites.draw(screen)

        for drawing in drawings:
            if not drawing.draw():
                drawings.remove(drawing)
            
        #pygame.draw.circle(pygame.display.get_surface(), Color(0,0,255,128), [250, 250], 30, 3)
        pygame.display.flip()

    
    while True:
        clock.tick(120)

    #Event Handling
        for event in pygame.event.get():
            if (event.type == QUIT
                or event.type == KEYDOWN 
                and event.key == K_ESCAPE):
                return False
            elif (event.type == KEYDOWN 
                and event.key == K_SPACE):
                return True

    #Update and draw all sprites 
        allsprites.update()
        screen.blit(background, (0,0))
        allsprites.draw(screen)
        pygame.display.flip()

                
if __name__ == '__main__':
    while(main()):
        pass
