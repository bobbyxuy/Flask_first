def test_kwargs(**kwargs):
   for k, v in kwargs.items():
      print('Optional argument %s (*kwargs): %s' % (k, v))