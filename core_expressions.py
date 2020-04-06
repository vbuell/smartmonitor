class Expression:
    pass

class Predicate:
    pass

class StatisticExpression:
    pass

class EntriesPredicate(Predicate):
    
    def of(self, name):
        pass

class LastPredicate(Predicate):
    
    def __init__(self, number):
        pass
    
    def entries(self):
        return EntriesPredicate()

    def minutes(self):
        return EntriesPredicate()

    def days(self):
        return EntriesPredicate()

def last(number):
    return LastPredicate(number)
