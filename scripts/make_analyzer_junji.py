from loadi.loaders.junji import JunjiSession

mouse = 8
day = 24
session_type = 'openfield'

analyzer_output_path = f"sub-{mouse}_day-{day}_ses-{session_type}_analyzer"

session = JunjiSession(mouse, day, session_type, active_projects_path="/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/")

# print("Making analyzer...")
analyzer = session.create_analyzer()

print("Saving analyzer...")
analyzer.save_as(format="binary_folder", folder=analyzer_output_path)