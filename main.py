import pygame
import os
import time
import random
import handDetectModule as hd
import cv2

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 500, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter Tutorial") 

# Load images
RED_enemy = pygame.image.load(os.path.join("assets", "enemy_red.png"))
GREEN_enemy = pygame.image.load(os.path.join("assets", "enemy_green.png"))
BLUE_enemy = pygame.image.load(os.path.join("assets", "enemy_blue.png"))

#Load music
pygame.mixer.music.load(os.path.join("assets", "Main_Music.wav"))
Damaged_Sound = pygame.mixer.Sound(os.path.join("assets", "Damaged_Sound.wav"))
Hit_Sound = pygame.mixer.Sound(os.path.join("assets", "Hit_Sound.wav"))
Gameover_Sound = pygame.mixer.Sound(os.path.join("assets", "Gameover_Sound.wav"))
Selection_Sound = pygame.mixer.Sound(os.path.join("assets", "Selection_Sound.wav"))
Shoot_Sound = pygame.mixer.Sound(os.path.join("assets", "Shoot_Sound.wav"))
Start_Sound = pygame.mixer.Sound(os.path.join("assets", "Start_Sound.wav"))
global Soundcheck
Soundcheck = True


# Player player
Fighter_Ship = pygame.image.load(os.path.join("assets", "fighter.png"))

# Lasers
RED_LASER = pygame.image.load(os.path.join("assets", "Laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "Laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "Laser_blue.png"))
Bullet = pygame.image.load(os.path.join("assets", "bullet.png"))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))
BGY = 0
BGY2 = BG.get_height()*-1
Logo = pygame.image.load(os.path.join("assets", "LOGO.png"))
Live = pygame.image.load(os.path.join("assets", "Live.png"))

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj, player=False):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                if player:
                    Damaged_Sound.play()
                
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(int((2*self.x+self.get_width())/2-self.laser_img.get_width()/2), self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = Fighter_Ship
        self.laser_img = Bullet
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        Hit_Sound.play()
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        for i in range(20):
            if self.health > (self.max_health//20)*i:
                pygame.draw.rect(window, (255,120,120), (10, HEIGHT-20-20*i, 40, 15))

class Enemy(Ship):
    COLOR_MAP = {
                "red": (RED_enemy, RED_LASER),
                "green": (GREEN_enemy, GREEN_LASER),
                "blue": (BLUE_enemy, BLUE_LASER)
                }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(int((2*self.x+self.get_width())//2-self.laser_img.get_width()/2), self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def main(mode):
    if mode == 'motion_mode':
        wCam, hCam = 800, 800

        cap = cv2.VideoCapture(0)
        cap.set(3, wCam)
        cap.set(4, hCam)

        pTime = 0
        detector = hd.handDetector(detectionCon=0.75)
        tipIds = [8, 12]
        totalFingers = 0

    run = True
    FPS = 60
    level = 0
    level_rank = [' ','F','D','C','B','A','S']
    lives = 5
    main_font = pygame.font.SysFont("comicsans", 35)
    lost_font = pygame.font.SysFont("comicsans", 60)

    enemies = []
    wave_length = 5
    enemy_vel = 1

    player_vel = 5
    laser_vel = 5

    player = Player(int(WIDTH/2-15), HEIGHT-35)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        # draw text
        Rank_label = main_font.render("Rank: "+level_rank[level], 1, (255,255,255))

        WIN.blit(Rank_label, (10, 50))

        for i in range(lives):
            WIN.blit(Live, (10+25*i,10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
            Final_label = lost_font.render("Your rank is "+level_rank[level], 1, (255,255,255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))
            WIN.blit(Final_label, (WIDTH/2 - Final_label.get_width()/2, 420))

        pygame.display.update()

    while run:
        if mode == 'motion_mode':
            success, img = cap.read()
    
            img = detector.findHands(img, draw=False)
            lmList, _ = detector.findPosition(img, draw=False)

            if len(lmList) != 0:
                fingers = []

                for id in [0,1]:
                    if lmList[tipIds[id]][2] < lmList[tipIds[id]-2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                totalFingers = fingers.count(1)
                print(lmList[8])

                if lmList[8][1]<200:
                    circleX = 200
                elif lmList[8][1]>400:
                    circleX = 400
                else:
                    circleX = lmList[8][1]

                if lmList[8][2]<25:
                    circleY = 25
                elif lmList[8][2]>305:
                    circleY = 305
                else:
                    circleY = lmList[8][2]

                cv2.circle(img, (circleX,circleY), 10, (255,0,0), cv2.FILLED)
                cv2.circle(img, (lmList[12][1],lmList[12][2]), 10, (255,0,0), cv2.FILLED)

            cTime = time.time()
            fps = 1/(cTime - pTime)
            
            cv2.putText(img, f'fps: {int(fps)}', (50, 120), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
            pTime = cTime

            cv2.rectangle(img, (200, 25), (400, 305), (0,0,0), 10)

            cv2.imshow("IMG", img)
            cv2.waitKey(1)

        clock.tick(FPS)
        global BGY
        global BGY2
        BGY += 0.4
        BGY2 += 0.4
        if BGY > BG.get_height():
            BGY = BG.get_height()*-1
        if BGY2 > BG.get_height():
            BGY2 = BG.get_height()*-1
        WIN.blit(BG, (0, BGY))
        WIN.blit(BG, (0, BGY2))
        redraw_window()
        
        if lives <= 0 or player.health <= 0:
            pygame.mixer.music.stop()
            lost = True
            lost_count += 1

        if lost:
            if lost_count == FPS:
                Gameover_Sound.play()
            if lost_count > FPS * 3:
                if Soundcheck:
                    pygame.mixer.music.play(-1)
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        if mode == 'keyboard_mode':
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] and player.x - player_vel > 0: # left
                player.x -= player_vel
            if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH: # right
                player.x += player_vel
            if keys[pygame.K_w] and player.y - player_vel > 0: # up
                player.y -= player_vel
            if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT: # down
                player.y += player_vel
            if keys[pygame.K_SPACE]:
                Shoot_Sound.play()
                player.shoot()
        elif mode == 'motion_mode':
            if len(lmList) != 0:
                player.x = int(((lmList[8][1]-200)*WIDTH//200))
                player.y = int(((lmList[8][2]-25)*WIDTH//280))
                if totalFingers == 2:
                    player.shoot()
            else:
                warn_font = pygame.font.SysFont("comicsans", 35)
                warn_label = warn_font.render("Hand is not detected!",1,(255,255,255))
                WIN.blit(warn_label, (WIDTH/2-warn_label.get_width()/2, 350))


        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player, player=True)

            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                Damaged_Sound.play()
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies)

def main_menu():
    global Soundcheck
    mode_font = pygame.font.SysFont("comicsans", 35)
    run = True
    selectionY = 400
    if Soundcheck == True:
        pygame.mixer.music.play()
    else:
        pygame.mixer.music.stop()
    while run:
        WIN.blit(BG, (0,0))
        WIN.blit(Logo, (int(WIDTH/2-Logo.get_width()/2), 100))

        keyboard_mode_label = mode_font.render("Play with keyboard", 1, (255,255,255))
        motion_mode_label = mode_font.render("Play with motion detection", 1, (255,255,255))
        option_label = mode_font.render("Option", 1, (255,255,255))
        credit_label = mode_font.render("Credit", 1, (255,255,255))
        WIN.blit(keyboard_mode_label, (WIDTH/2 - 160, 400))
        WIN.blit(motion_mode_label, (WIDTH/2 - 160, 450))
        WIN.blit(option_label, (WIDTH/2 - 160, 500))
        WIN.blit(credit_label, (WIDTH/2 - 160, 550))
        pygame.draw.polygon(WIN, (255,255,255), [[WIDTH/2-200,selectionY],[WIDTH/2-200,selectionY+20],[WIDTH/2-170,selectionY+10]])

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if selectionY == 400:
                        Start_Sound.play()
                        main('keyboard_mode')
                    elif selectionY == 450:
                        Start_Sound.play()
                        main('motion_mode')
                    elif selectionY == 500:
                        Start_Sound.play()
                        option_menu()
                    elif selectionY == 550:
                        Start_Sound.play()
                        credit_menu()
                elif event.key == pygame.K_s:
                    if selectionY >= 550:
                        selectionY += 0
                    else:
                        Selection_Sound.play()
                        selectionY += 50
                elif event.key == pygame.K_w:
                    if selectionY <= 400:
                        selectionY -= 0
                    else:
                        Selection_Sound.play()
                        selectionY -= 50
    pygame.quit()

def credit_menu():
    mode_font = pygame.font.SysFont("comicsans", 27)
    run = True

    while run:
        WIN.blit(BG, (0,0))

        label1 = mode_font.render("Daeho Go", 1, (255,255,255))
        label2 = mode_font.render("Seungjoon Yang", 1, (255,255,255))
        label3 = mode_font.render("Junghoon Oh", 1, (255,255,255))
        label4 = mode_font.render("Music special thanks to Seungwoo Yang", 1, (255,255,255))
        WIN.blit(label1, (WIDTH/2 - 160, 200))
        WIN.blit(label2, (WIDTH/2 - 160, 250))
        WIN.blit(label3, (WIDTH/2 - 160, 300))
        WIN.blit(label4, (WIDTH/2 - 160, 400))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    run = False

def option_menu():
    
    global Soundcheck
    Soundcheck = True
    mode_font = pygame.font.SysFont("comicsans", 35)
    run = True
    selectionY = 400
    
    while run:
        WIN.blit(BG,(0,0))
        soundon_label = mode_font.render("Sound ON", 1, (255,255,255))
        soundoff_label = mode_font.render("Sound OFF", 1, (255,255,255))
        Back_label = mode_font.render("Back", 1, (255,255,255))
        WIN.blit(soundon_label, (WIDTH/2 - 160, 400))
        WIN.blit(soundoff_label, (WIDTH/2 - 160, 450))
        WIN.blit(Back_label, (WIDTH/2 - 160, 500))
        pygame.draw.polygon(WIN, (255,255,255), [[WIDTH/2-200,selectionY],[WIDTH/2-200,selectionY+20],[WIDTH/2-170,selectionY+10]])
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if selectionY == 400:
                        Start_Sound.play()
                        pygame.mixer.music.play()
                        Soundcheck = True
                    elif selectionY == 450:
                        Start_Sound.play()
                        pygame.mixer.music.stop()
                        Soundcheck = False
                    elif selectionY == 500:
                        Start_Sound.play()
                        main_menu()
                elif event.key == pygame.K_s:
                    if selectionY >= 500:
                        selectionY += 0
                    else:
                        Selection_Sound.play()
                        selectionY += 50
                elif event.key == pygame.K_w:
                    if selectionY <= 400:
                        selectionY -= 0
                    else:
                        Selection_Sound.play()
                        selectionY -= 50
           
        
      
    pygame.quit()


main_menu()