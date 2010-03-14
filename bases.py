class Bases():
    def __init__(self):
        self.bases  = [False,False,False]
        self.runs   = 0

    def get_base(self, base):
        return self.bases[base-1]

    def process_event(self, player, event):
        if event == "walk":
            self.bases.insert(0,player)
            i=0
            removed_base = False
            for base in self.bases:
                if base == False and removed_base == False:
                    self.bases.pop(i)
                    removed_base = True
                i+=1    
            if removed_base == False:
                self.bases.pop()
                self.runs += 1
        if event == "single":
            self.bases.insert(0,player)
            if self.bases.pop() != False:
                self.runs += 1
        if event == "double":
            self.bases.insert(0,player)
            self.bases.insert(0,False)
            if self.bases.pop() != False:
                self.runs +=1
            if self.bases.pop() != False:
                self.runs +=1
        if event == "triple":
            for base in self.bases:
                if base != False:
                    self.runs +=1
            self.bases = [False,False,player]
        if event == "HR":
            for base in self.bases:
                if base != False:
                    self.runs +=1
            self.runs += 1
            self.bases = [False,False,False]

        #print self.bases, self.runs
