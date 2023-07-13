/* This is free and unencumbered software released into the public domain. https://unlicense.org/

Trying to get some interesting looking lens flares, seems like it worked.
See https://www.shadertoy.com/view/lsBGDK for a more avanced, generalized solution

If you find this useful send me an email at peterekepeter at gmail dot com,
I've seen this shader pop up before in other works, but I'm curious where it ends up.

If you want to use it, feel free to do so, there is no need to credit but it is appreciated.


Used in:

 Water World - https://www.shadertoy.com/view/lslGDB

 Floating Mountains - https://www.shadertoy.com/view/XsSGDy

 Clouds and Sun With Flare - https://www.shadertoy.com/view/4sl3zl

 musk's lens flare mod - https://www.shadertoy.com/view/XdfXRX

 Land of Dreams - https://github.com/Tomius/LoD

 Where is Starman? - https://spacein3d.com/starman


Changelog:

 13/08/13:
	first published

 17/11/27
    fixed seam, thanks to Shane

 19/08/08:
    updated description and license change

 20/06/24:
    renamed to Lens Flare Example, updated description

*/
#version 330

uniform vec2 iResolution;
uniform vec3 iPos;
uniform vec2 iShift;


vec3 lensflare(vec2 uv,vec2 pos)
{
	vec2 main = uv-pos;
	vec2 uvd = uv*(length(uv));

	float dist=pow(length(main), 0.1);

	float f0 = 0.6/(length(uv-pos)*16.0 + 1.0);
//	f0 = 1.0 / (pow(length(main), 0.1) + 1.0);

	f0 = f0 + f0*(dist*.1 + .8);//	f0 = f0 * dist * 5;

	float f1 = max(0.01-pow(length(uv+1.2*pos),1.9),.0)*7.0;

	float f2 = max(1.0/(1.0+32.0*pow(length(uvd+0.8*pos),2.0)),.0)*00.25;
	float f22 = max(1.0/(1.0+32.0*pow(length(uvd+0.85*pos),2.0)),.0)*00.23;
	float f23 = max(1.0/(1.0+32.0*pow(length(uvd+0.9*pos),2.0)),.0)*00.21;

	vec2 uvx = mix(uv,uvd,-0.5);

	float f4 = max(0.01-pow(length(uvx+0.4*pos),2.4),.0)*6.0;
	float f42 = max(0.01-pow(length(uvx+0.45*pos),2.4),.0)*5.0;
	float f43 = max(0.01-pow(length(uvx+0.5*pos),2.4),.0)*3.0;

	uvx = mix(uv,uvd,-.4);

	float f5 = max(0.01-pow(length(uvx+0.2*pos),5.5),.0)*2.0;
	float f52 = max(0.01-pow(length(uvx+0.4*pos),5.5),.0)*2.0;
	float f53 = max(0.01-pow(length(uvx+0.6*pos),5.5),.0)*2.0;

	uvx = mix(uv,uvd,-0.5);

	float f6 = max(0.01-pow(length(uvx-0.3*pos),1.6),.0)*6.0;
	float f62 = max(0.01-pow(length(uvx-0.325*pos),1.6),.0)*3.0;
	float f63 = max(0.01-pow(length(uvx-0.35*pos),1.6),.0)*5.0;

	vec3 c = vec3(.0);

	c.r += f2 +f4+f5+f6;
	c.g += f22+f42+f52+f62;
	c.b += f23+f43+f53+f63;
//	c = c*1.3- vec3(length(uvd)*.05);
	c = c*(0.7 + length(uvd)*4);
//	c *= 0.5;

	c += vec3(f0);

	return c;
}

vec3 cc(vec3 color, float factor,float factor2) // color modifier
{
	float w = color.x+color.y+color.z;
	return mix(color,vec3(w)*factor,w*factor2);
}

void main()
{
	vec2 uv = (gl_FragCoord.xy)/ iResolution.xy - 0.5 - iShift.xy;
	uv.x *= iResolution.x/iResolution.y; //fix aspect ratio
	vec2 mouse = iPos.xy; ///iResolution.xy - 0.5;
	mouse.x *= iResolution.x/iResolution.y; //fix aspect ratio

	vec3 color = vec3(1.4,1.2,1.0) * lensflare(uv, mouse.xy);
	color = cc(color,.5,.1);
	gl_FragColor = vec4(color, (color.r + color.g + color.b) / 3.0);
}