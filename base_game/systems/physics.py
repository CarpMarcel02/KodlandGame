from pygame import Rect

def move_and_collide(rect: Rect, dx: float, dy: float, solids: list[Rect]) -> bool:

    hit_bottom = False

    if dx:
        rect.x += int(round(dx))
        for s in solids:
            if rect.colliderect(s):
                if dx > 0:
                    rect.right = s.left
                else:
                    rect.left = s.right

    if dy:
        rect.y += int(round(dy))
        for s in solids:
            if rect.colliderect(s):
                if dy > 0:           
                    rect.bottom = s.top
                    hit_bottom = True
                else:                
                    rect.top = s.bottom

    return hit_bottom
