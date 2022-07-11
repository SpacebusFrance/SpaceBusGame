from engine.main_engine import Game

# quality_level = 0
# test = 0
# scenario = "default"
#
# # reading second arg if present
# if len(sys.argv) == 2:
#     print('Quality = ', sys.argv[1])
#     quality_level = int(sys.argv[1])

game = Game(param_file='params.ini', default_param_file='params_default.ini')
# game.start_game()
game.run()
