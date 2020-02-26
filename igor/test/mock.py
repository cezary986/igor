
class IgorMock():

  def __init__(self):
    self.clients = {}
    self.server = IgorServerMock()

class IgorServerMock():
  
  def __init__(self):
    self.send_message = None

class ClientMock():

  def __init__(self, client_id):
    self.id = client_id