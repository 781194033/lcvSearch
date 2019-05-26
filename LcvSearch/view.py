# -*- coding: utf-8 -*-
import json
import redis
from django.shortcuts import render
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
es = Elasticsearch()
redis_cli = redis.StrictRedis()

title = "标题"
abstract = "摘要"
def filter_type(data):
	hits = data['hits']['hits']
	data_list = []
	for i in hits:
		i["_source"]["_id"] = i["_id"]
		i["_source"]["_index"] = i["_index"]
		data_list.append(i["_source"])
	return data_list

def delete_by_id(req):
	if req.method == "POST":
		_id = req.POST.get("id","")
		_index = req.POST.get("index","")
		if _id and _index:
			try:
				es.delete_by_query(index=_index,body={"query":{"term":{"_id":_id}}})
				return HttpResponse(json.dumps({"status":0,"msg":"删除成功"}),content_type="application/json")
			except:
				return HttpResponse(json.dumps({"status":0,"msg":"删除失败"}),content_type="application/json")


def get_top_ten(req):
	topn_search = redis_cli.zrevrangebyscore("search_keywords_set","+inf","-inf",start=0,num=10)
	for i in range(0,len(topn_search)):
		topn_search[i] = topn_search[i].decode()
	return HttpResponse(json.dumps({"status":0,"data":{"list":topn_search}}),content_type="application/json")


def patent_list(req):
	if req.method == "POST":
		search_type = req.POST.get('searchType','ti')
		search_keyword = req.POST.get('searchKeyword','')
		page = int(req.POST.get('pageNum',"1"))

		# 用户没有输入关键词
		if search_keyword == '':
			result = es.search(
				index=search_type,
				body={
				  "query": {
				    "match_all": {}
				  },
				  "from":(page-1)*10,
				  "size":10
				}
			)
			total = result['hits']['total']
			result = filter_type(data=result)
			return HttpResponse(json.dumps({"status":0,"data":{"list":result,"total":total}}),content_type="application/json")
		#用户有输入关键词		
		result = es.search(
			index=search_type,
			body={
				"query": {
					"match":{
						title:search_keyword
					}
				},
				"from":(page-1)*10,
				"size":10
		    }
		)
		total = result['hits']['total']
		result = filter_type(data=result)
		return HttpResponse(json.dumps({"status":0,"data":{"list":result,"total":total}}),content_type="application/json")


# 首页
def index(request):
	statistic()
	res_data = {}
	user = request.session.get("CURRENT_USER")
	if user:
		res_data["user"] = user
	else:
		res_data["user"] = ''
	res_data["topn_search"] = top_n()
	return render(request, 'index.html', res_data)

# 结果列表页
def search(req):
	statistic()
	key_words = req.GET.get('q','')
	page = req.GET.get('p','1')
	s_type = req.GET.get('s_type','ti')
	if s_type == "ti":
		_abstract = '摘要 (原文)'
	else:
		_abstract = abstract
		
	try:
		page = int(page)
	except:
		page = 1

	if key_words:
		redis_cli.zincrby(name='search_keywords_set',value=key_words,amount=1)

		start_time = datetime.now()
		result = items_search(page=page,key_words=key_words,s_type=s_type);
		end_time = datetime.now()

		total = result['hits']['total']
		guess_you_like = []
		more_like_this = es.search(
			index=s_type,
			body={
			  "query": {
			    "more_like_this": {
			      "fields": [
			        _abstract
			      ],
			      "like_text":key_words ,
			      "min_term_freq": 1,
			      "max_query_terms": 12
			    }
			}
		})['hits']['hits']
		for source in more_like_this:
			guess_you_like.append(source['_source'][title])
		res_data = {
			"all_hits":data_parse(result,s_type),
			"key_words":key_words,
			"total_nums":total,
			"page":page,
			"page_nums":num_of_page(total),
			"search_time":(end_time-start_time).total_seconds(),
			"ti_count":redis_cli.get('ti_count').decode(),
			"topn_search":top_n(),
			"textile_count":redis_cli.get("textile_count").decode(),
			"costume_count":redis_cli.get("costume_count").decode(),
			"guess_you_like":list(set(guess_you_like))[:3]
		}
		return render(req,"result.html",res_data)
	return render(req,"result.html")

# 搜索建议接口
def suggest(req):
	key_words = req.GET.get('s','')
	s_type = req.GET.get('s_type','')

	res_data =[]
	suggestions = es.search(
	    index=s_type,
	    body={
	        "suggest":{
	            "my_suggest":{
	                "text": key_words,
	                "completion":{
	                    "field":"suggest"
	                }
	            }
	        },
	        "size":10
	    }
	)
	for match in suggestions['suggest']['my_suggest'][0]['options']:
		res_data.append(match["_source"][title][:75])

	return HttpResponse(json.dumps(res_data),content_type="application/json")



def get_statistic(req):
	user = req.session.get("CURRENT_USER")
	if user:
		res_data = {
			"status":0,
			"data":{
				"TIcount" : redis_cli.get("ti_count").decode(),
				"costomCount" : redis_cli.get("costome_count").decode(),
				"textileCount" : redis_cli.get("textile_count").decode(),
				"visitedCount" : redis_cli.get("visited_count").decode()
			}
		}
	else:
		res_data = {
			"status":10,
			"msg":"用户未登录"
		}
	return HttpResponse(json.dumps(res_data),content_type="application/json")






def data_parse(result,s_type):
	if s_type == "ti":
		_abstract = '摘要 (原文)'
	else:
		_abstract = abstract

	hit_list = []
	for hit in result['hits']['hits']:
		hit_dict = {}
		if title in hit['highlight']:
			hit_dict["title"] =  " ".join(hit['highlight'][title])
		else:
			hit_dict["title"] =  " ".join(hit['_source'][title])

		if _abstract in hit['highlight']:
			hit_dict["abstract"] =  " ".join(hit['highlight'][_abstract])
		else:
			hit_dict["abstract"] =  " ".join(hit['_source'][_abstract])

		hit_list.append(hit_dict)
	return hit_list

def num_of_page(total):
	return int(total/10) if total%10 <= 0 else int(total/10) + 1
# 热门搜索
def top_n():
	topn_search = redis_cli.zrevrangebyscore("search_keywords_set","+inf","-inf",start=0,num=5)
	for i in range(0,len(topn_search)):
			topn_search[i] = topn_search[i].decode()
	return topn_search

# 统计pv,uv等
def statistic():
	# 访问次数
	redis_cli.incr("visited_count")


def items_search(page,key_words,s_type):
	if s_type == "ti":
		_abstract = '摘要 (原文)'
	else:
		_abstract = abstract

	result = es.search(
		index=s_type,
		body={
		  "query": {
		    "multi_match": {
		      "query": key_words,
		      "fields": [
		        title,
		        _abstract
		      ]
		    }
		  },
		  "from":(page-1)*10,
		  "size":10,
		  "highlight": {
		    "pre_tags": [
		      "<span class='keyWord'>"
		    ],
		    "post_tags": [
		      "</span>"
		    ],
		    "fields": {
		      title: {},
		      _abstract:{}
		    }
		  }
		}
	)
	return result