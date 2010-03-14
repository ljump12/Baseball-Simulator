class Bases():
    """ This class will attempt to model the bases, and how events
        affect the bases.

        A couple of assumptions are made:
        1.  A single moves every runner up one base.
        2.  A double moves every runner up two bases.

        TODO:: Model Stolen bases, double plays etc.
    """

    def __init__(self):
        """ Initializes our bases to empty, also initializes the
            'innings' runs to empty
        """
        self.bases  = [False,False,False]
        self.runs   = 0

    def get_base(self, base):
        """ Returns the current player on the base, returns False
            if the base is empty
        """
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
