from loadi.loaders.junji import JunjiSession

mouse = 8
day = 24
session = 'openfield'

session = JunjiSession(mouse, day, session, active_projects_path="/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/")

clusters = session.get_clusters()
analyzer = session.create_analyzer()
analyzer.save_as(format="binary_folder", folder=f"sub-{mouse}_day-{day}_ses-{session}_analyzer")