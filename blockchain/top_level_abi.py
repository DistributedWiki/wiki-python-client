abi = """[
	{
		"constant": false,
		"inputs": [
			{
				"name": "titleHash",
				"type": "bytes32"
			},
			{
				"name": "ID",
				"type": "bytes32"
			}
		],
		"name": "createArticle",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"constant": true,
		"inputs": [
			{
				"name": "titleHash",
				"type": "bytes32"
			}
		],
		"name": "getArticle",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	}
]
"""
