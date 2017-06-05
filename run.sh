#./analyze_lost.py <pred_result> <ground_truth_lable> <id_name_map> <black_list_repo_dir> <iou_thresh> <similarity_score_thresh> 

####DG
#当前VSD
#./analyze_lost.py ~/result.txt ./exp_data/dg/ground_truth/label.txt ./exp_data/dg/id_name_map.txt ./black_list_repo 0.3 0.6


# multi_vote 
#./analyze_lost.py ./result.txt ./ground_truth/dg/ground_truth/label.txt ./exp_data/dg/id_name_map_hg.txt ./black_list_repo 0.3 0.6

# single_vote 
#./analyze_lost.py ./result.txt ./ground_truth/dg/ground_truth/label.txt ./exp_data/dg/id_name_map_hg.txt ./black_list_repo 0.3 0.6

# 更新tracking 
#./analyze_lost.py ./result.txt ./ground_truth/dg/ground_truth/label.txt ./exp_data/dg/id_name_map_hg.txt ./black_list_repo 0.3 0.6

#===================================================================
####haiguan
#./analyze_lost.py ~/haiguan_result_19_track3.1.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./black_list_repo_167 0.3 0.86
#./analyze_lost.py ~/result.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./black_list_repo_162 0.3 0.90
./analyze_lost.py ~/result.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./ziyong_black_list 0.3 0.90
#./analyze_lost.py ~/haiguan_result_19_track3.1_M0.7.7.1.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./black_list_repo_162 0.3 0.83
#./analyze_lost.py ~/result.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./black_list_repo_162 0.3 0.75
#./analyze_lost.py ~/result.txt ./exp_data/haiguan/ground_truth/label.txt ./exp_data/haiguan/id_name_map.txt ./black_list_repo_167 0.3 0.84

####dalian1
#./analyze_lost.py ~/result.txt ./exp_data/dalian1/ground_truth/label.txt ./exp_data/dalian1/id_name_map.txt ./black_list_repo_162 0.0 0.0
