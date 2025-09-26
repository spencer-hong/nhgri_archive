import { TSMap } from "typescript-map"

function postData(action: any, kwargs: TSMap<any, any> |  null, chain: boolean): void {
	let digest_list: any = [];
	let action_list: any = [];
	console.log("action");
	console.log(action);
	if (kwargs == null && chain) {
		for (let i = 0; i < action.length; i++) {
			digest_list.push({
				"action": action[i]['action']
			});
		  }

	}
	else if (kwargs == null ) {
		digest_list = [
		    {
		         
		        "action": action
		    }];
	}
	else if (kwargs != null && chain) {
		for (let i = 0; i < action.length; i++) {
			digest_list.push({
				"action": action[i]['action'],
				"kwargs": action[i]['kwargs']
			});
		  }

	}
	else {

		var kwargs_send = kwargs.toJSON();
	digest_list = [
	    {
	         
	        "action": action,
	         'kwargs': kwargs_send
	    }];
	}
	if (chain) {
		action_list = { 
            "action_list": digest_list 
        }

		console.log(action_list);
	fetch("/api/action/chain", {
	method: "POST",
	headers: {
	'Content-Type' : 'application/json'
	},
	body: JSON.stringify(action_list)
	});

	}
	else {
		action_list = {
			"action_list": digest_list
		}

		console.log(action_list);
	fetch("/api/action/concurrent", {
	method: "POST",
	headers: {
	'Content-Type' : 'application/json'
	},
	body: JSON.stringify(action_list)
	});


	}

    
}


export default postData;