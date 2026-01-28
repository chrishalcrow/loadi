from loadi.loaders.bri import BriSession
import spikeinterface.full as si

mouse = '1543'
date = '2023-02-13'
session = 'obj'

session = BriSession(mouse, date, session)

clusters = session.get_clusters()
positions = session.get_position()

Px = positions['Px']
Py = positions['Py']

analyzer = session.create_analyzer()
