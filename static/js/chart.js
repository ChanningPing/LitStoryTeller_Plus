/**
 * Created by qingping on 12/25/16.
 */
/**
 * Created by qingping on 12/25/16.
 */
// Request the data

d3.json('data/data1.json', function(err, response){

	var svg, scenes, charactersMap, width, height, sceneWidth;

	// Get the data in the format we need to feed to d3.layout.narrative().scenes
	scenes = wrangle(response);

	// Some defaults
	sceneWidth = 10;
	width = scenes.length * sceneWidth * 4;
	height = 600;
	labelSize = [150,15];

	// The container element (this is the HTML fragment);
	svg = d3.select("body").append('svg')
		.attr('id', 'narrative-chart')
		.attr('width', width)
		.attr('height', height);

	// Calculate the actual width of every character label.
	scenes.forEach(function(scene){
		scene.characters.forEach(function(character) {
			character.width = svg.append('text')
				.attr('opacity',0)
				.attr('class', 'temp')
				.text(character.name)
					.node().getComputedTextLength()+10;
		});
	});

	// Remove all the temporary labels.
	svg.selectAll('text.temp').remove();

	// Do the layout
	narrative = d3.layout.narrative()
		.scenes(scenes)
		.size([width,height])
		.pathSpace(10)
		.groupMargin(10)
		.labelSize([250,15])
		.scenePadding([5,sceneWidth/2,5,sceneWidth/2])
		.labelPosition('left')
		.layout();

	// Get the extent so we can re-size the SVG appropriately.
	svg.attr('height', narrative.extent()[1]);

	// Draw the scenes
	svg.selectAll('.scene').data(narrative.scenes()).enter()
		.append('g').attr('class', 'scene')
			.attr('transform', function(d){
					var x,y;
					x = Math.round(d.x)+0.5;
					y = Math.round(d.y)+0.5;
					return 'translate('+[x,y]+')';
				})
			.append('rect')
				.attr('width', sceneWidth)
				.attr('height', function(d){
					return d.height;
				})
				.attr('y', 0)
				.attr('x', 0)
				.attr('rx', 3)
				.attr('ry', 3);

	// Draw appearances
	svg.selectAll('.scene').selectAll('.appearance').data(function(d){
		return d.appearances;
	}).enter().append('circle')
		.attr('cx', function(d){
			return d.x;
		})
		.attr('cy', function(d){
			return d.y;
		})
		.attr('r', function(){
			return 2;
		})
		.attr('class', function(d){
			return 'appearance ' + d.character.affiliation;
		});

	// Draw links
	svg.selectAll('.link').data(narrative.links()).enter()
		.append('path')
		.attr('class', function(d) {
			return 'link ' + d.character.affiliation.toLowerCase();
		})
		.attr('d', narrative.link());

	// Draw intro nodes
	svg.selectAll('.intro').data(narrative.introductions())
		.enter().call(function(s){
			var g, text;

			g = s.append('g').attr('class', 'intro');

			g.append('rect')
				.attr('y', -4)
				.attr('x', -4)
				.attr('width', 4)
				.attr('height', 8);

			text = g.append('g').attr('class','text');

			// Apppend two actual 'text' nodes to fake an 'outside' outline.
			text.append('text');
			text.append('text').attr('class', 'color');

			g.attr('transform', function(d){
					var x,y;
					x = Math.round(d.x);
					y = Math.round(d.y);
					return 'translate(' + [x,y] + ')';
				});

			g.selectAll('text')
				.attr('text-anchor', 'end')
				.attr('y', '4px')
				.attr('x', '-8px')
				.text(function(d){ return d.character.name; });

			g.select('.color')
				.attr('class', function(d){
					return 'color ' + d.character.affiliation;
				});

			g.select('rect')
				.attr('class', function(d){
					return d.character.affiliation;
				});

		});

});

function wrangle(data) {

	var charactersMap = {};

	return data.scenes.map(function(scene){
		return {characters: scene.map(function(id){
			return characterById(id);
		}).filter(function(d) { return (d); })};
	});

	// Helper to get characters by ID from the raw data
	function characterById(id) {
		charactersMap = charactersMap || {};
		charactersMap[id] = charactersMap[id] || data.characters.find(function(character){
			return character.id === id;
		});
		return charactersMap[id];
	}

}


